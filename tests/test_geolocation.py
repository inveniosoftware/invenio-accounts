# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test the country lookup: iptocc by default, a MaxMind DB if configured."""

import logging
import os
import sys

import pytest

from invenio_accounts.geolocation import _open_mmdb, ip2country

CERN_IP = "188.184.9.234"  # iptocc says "CH"
EU_IP = "139.191.247.1"  # registered as "EU" by RIPE


def test_ip2country_default_uses_iptocc(app):
    """Without the setting, the country comes from iptocc."""
    with app.app_context():
        assert app.config.get("ACCOUNTS_GEOIP_DB_PATH") is None
        assert ip2country(CERN_IP) == "CH"
        assert ip2country("127.0.0.1") is None
        assert ip2country("") is None
        assert ip2country(None) is None


@pytest.mark.parametrize("empty", [None, ""])
def test_ip2country_empty_setting_uses_iptocc(app, empty):
    """An empty setting is the same as no setting."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = empty
    with app.app_context():
        assert ip2country(CERN_IP) == "CH"


def test_ip2country_eu_is_not_a_country(app):
    """The registry placeholder "EU" is stored as no country."""
    with app.app_context():
        assert ip2country(EU_IP) is None


def test_ip2country_uses_mmdb(app, make_mmdb, caplog):
    """If the setting is set, the answer comes from the file, not from iptocc."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb(
        {"188.184.0.0/16": "DE", "2001:db8::/32": "FR"}
    )
    with app.app_context(), caplog.at_level(logging.ERROR):
        # iptocc would say "CH" here
        assert ip2country(CERN_IP) == "DE"
        assert ip2country("2001:db8::1") == "FR"
        # An IP that is not in the file has no country. iptocc would say "US",
        # so this also shows that a working file never falls back.
        assert ip2country("8.8.8.8") is None
    assert caplog.records == []


def test_ip2country_mmdb_eu_is_not_a_country(app, make_mmdb):
    """ "EU" is stored as no country for a MaxMind DB as well."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb({"139.191.0.0/16": "EU"})
    with app.app_context():
        assert ip2country(EU_IP) is None


@pytest.mark.parametrize("bad_ip", ["nonsense", "999.1.1.1", "1.2.3", "::g"])
def test_ip2country_mmdb_invalid_ip(app, make_mmdb, caplog, bad_ip):
    """An invalid IP is no country, and is not a configuration error."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb({"188.184.0.0/16": "DE"})
    with app.app_context(), caplog.at_level(logging.ERROR):
        assert ip2country(bad_ip) is None
    assert caplog.records == []


def test_ip2country_mmdb_ipv4_only_file(app, make_mmdb, caplog):
    """An IPv6 address in a file that only has IPv4 is no country."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb(
        {"188.184.0.0/16": "DE"}, ip_version=4
    )
    with app.app_context(), caplog.at_level(logging.ERROR):
        assert ip2country(CERN_IP) == "DE"
        assert ip2country("2001:db8::1") is None
    assert caplog.records == []


def test_ip2country_mmdb_record_without_country(app, tmp_path, caplog):
    """A record without a country is no country."""
    from mmdb_writer import MMDBWriter
    from netaddr import IPSet

    writer = MMDBWriter(
        ip_version=6,
        ipv4_compatible=True,
        database_type="Test-City",
        languages=["en"],
        description={"en": "test database"},
    )
    writer.insert_network(IPSet(["188.184.0.0/16"]), {"continent": {"code": "EU"}})
    path = tmp_path / "city.mmdb"
    writer.to_db_file(str(path))

    app.config["ACCOUNTS_GEOIP_DB_PATH"] = str(path)
    with app.app_context(), caplog.at_level(logging.ERROR):
        assert ip2country(CERN_IP) is None
    assert caplog.records == []


@pytest.mark.parametrize("kind", ["missing", "garbage", "empty", "directory"])
def test_ip2country_unreadable_file_falls_back(app, tmp_path, caplog, kind):
    """A file that cannot be read is logged as an error and iptocc is used."""
    path = tmp_path / "geo.mmdb"
    if kind == "garbage":
        path.write_bytes(b"this is not a MaxMind DB" * 100)
    elif kind == "empty":
        path.write_bytes(b"")
    elif kind == "directory":
        path.mkdir()

    app.config["ACCOUNTS_GEOIP_DB_PATH"] = str(path)
    with app.app_context(), caplog.at_level(logging.ERROR):
        assert ip2country(CERN_IP) == "CH"  # from iptocc
        assert ip2country(EU_IP) is None  # the fallback maps "EU" as well

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 2  # logged on every lookup, so it is not missed
    for record in errors:
        assert "ACCOUNTS_GEOIP_DB_PATH" in record.getMessage()
        assert str(path) in record.getMessage()
        assert record.exc_info is not None  # includes the traceback
        # the IP address is personal data and must not be logged
        assert CERN_IP not in record.getMessage()
        assert EU_IP not in record.getMessage()


def test_ip2country_mmdb_recovers_when_file_appears(app, make_mmdb, tmp_path, caplog):
    """A failed open is not cached, so fixing the file needs no restart."""
    path = tmp_path / "geo.mmdb"
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = str(path)
    with app.app_context(), caplog.at_level(logging.ERROR):
        assert ip2country(CERN_IP) == "CH"  # missing: iptocc
        assert len(caplog.records) == 1

        make_mmdb({"188.184.0.0/16": "DE"}, name="geo.mmdb")
        assert ip2country(CERN_IP) == "DE"
        assert len(caplog.records) == 1  # no new error


def test_ip2country_mmdb_picks_up_replaced_file(app, make_mmdb):
    """A file that is replaced on disk is read again without a restart."""
    path = make_mmdb({"188.184.0.0/16": "DE"})
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = path
    with app.app_context():
        assert ip2country(CERN_IP) == "DE"

        old = os.stat(path).st_mtime_ns
        make_mmdb({"188.184.0.0/16": "FR"})
        # make sure that the modification time changes on coarse file systems
        os.utime(path, ns=(old + 10**9, old + 10**9))
        assert ip2country(CERN_IP) == "FR"


def test_ip2country_mmdb_replaced_file_keeping_mtime(app, make_mmdb, tmp_path):
    """A file replaced by a rename is read again, even with the same mtime and size.

    Tools like ``rsync -t`` or ``cp -p`` keep the modification time, and the
    new database can have the same size. Only the inode is different.
    """
    path = make_mmdb({"188.184.0.0/16": "DE"})
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = path
    with app.app_context():
        assert ip2country(CERN_IP) == "DE"

        old = os.stat(path)
        new_path = make_mmdb({"188.184.0.0/16": "FR"}, name="new.mmdb")
        os.utime(new_path, ns=(old.st_atime_ns, old.st_mtime_ns))
        os.replace(new_path, path)
        new = os.stat(path)
        # the point of the test: only the inode is different
        assert (new.st_mtime_ns, new.st_size) == (old.st_mtime_ns, old.st_size)
        assert new.st_ino != old.st_ino

        assert ip2country(CERN_IP) == "FR"


def test_ip2country_mmdb_rewritten_file_keeping_mtime(app, make_mmdb):
    """A file that is written in place is read again if its size changes."""
    path = make_mmdb({"188.184.0.0/16": "DE"})
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = path
    with app.app_context():
        assert ip2country(CERN_IP) == "DE"
        assert ip2country("2001:db8::1") is None

        old = os.stat(path)
        make_mmdb({"188.184.0.0/16": "FR", "2001:db8::/32": "NL"})
        os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
        new = os.stat(path)
        # the point of the test: only the size is different
        assert new.st_mtime_ns == old.st_mtime_ns
        assert new.st_ino == old.st_ino
        assert new.st_size != old.st_size

        assert ip2country(CERN_IP) == "FR"
        assert ip2country("2001:db8::1") == "NL"


def test_ip2country_mmdb_reader_is_reused(app, make_mmdb):
    """The file is opened once, not for every lookup."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb({"188.184.0.0/16": "DE"})
    with app.app_context():
        for _ in range(5):
            assert ip2country(CERN_IP) == "DE"
    info = _open_mmdb.cache_info()
    assert (info.misses, info.hits) == (1, 4)


def test_ip2country_maxminddb_not_installed_falls_back(
    app, make_mmdb, caplog, monkeypatch
):
    """If maxminddb cannot be imported, it is an error and iptocc is used."""
    app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb({"188.184.0.0/16": "DE"})
    monkeypatch.setitem(sys.modules, "maxminddb", None)  # import raises
    with app.app_context(), caplog.at_level(logging.ERROR):
        assert ip2country(CERN_IP) == "CH"
    assert len(caplog.records) == 1
    assert "ACCOUNTS_GEOIP_DB_PATH" in caplog.records[0].getMessage()


def test_ip2country_setting_is_read_for_every_lookup(app, make_mmdb):
    """Changing the setting at runtime changes the source."""
    with app.app_context():
        assert ip2country(CERN_IP) == "CH"
        app.config["ACCOUNTS_GEOIP_DB_PATH"] = make_mmdb({"188.184.0.0/16": "DE"})
        assert ip2country(CERN_IP) == "DE"
        app.config["ACCOUNTS_GEOIP_DB_PATH"] = None
        assert ip2country(CERN_IP) == "CH"
