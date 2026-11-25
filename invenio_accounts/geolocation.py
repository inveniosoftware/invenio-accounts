# SPDX-FileCopyrightText: 2015-2026 CERN.
# SPDX-License-Identifier: MIT

"""Find the country of an IP address.

Uses ``iptocc`` by default, or a MaxMind DB file if its path is configured.
"""

import os
from functools import lru_cache

from flask import current_app
from iptocc import country_code


def _file_signature(path):
    """Return a value that changes when the file at ``path`` is replaced.

    The modification time alone is not enough: it can be kept by the tool that
    copies the file, and it can be too coarse on some file systems. The size
    catches most of those. The inode catches a file that is written next to
    the old one and renamed over it, which is the safe way to refresh a file.
    """
    stat = os.stat(path)
    return stat.st_mtime_ns, stat.st_size, stat.st_ino


@lru_cache(maxsize=2)
def _open_mmdb(path, signature):
    """Open the MaxMind DB at ``path``.

    ``signature`` is only part of the cache key, so that a file that was
    replaced on disk (e.g. by a monthly refresh) is opened again.
    """
    # Imported here so that it is only loaded when the setting is used.
    import maxminddb

    return maxminddb.open_database(path)


def _mmdb_country(path, ip):
    """Look up ``ip`` in the MaxMind DB at ``path``."""
    reader = _open_mmdb(path, _file_signature(path))
    try:
        record = reader.get(ip)
    except ValueError:  # not a valid IP address
        return None
    return (record or {}).get("country", {}).get("iso_code")


def ip2country(ip):
    """Get the ISO country code of ``ip``, or ``None``.

    Uses the MaxMind DB from ``ACCOUNTS_GEOIP_DB_PATH`` if it is set, and
    ``iptocc`` otherwise. If the file cannot be read, logs the error and uses
    ``iptocc``. An IP that is not in the file gives ``None``.


    :param ip: The IP address.
    """
    if not ip:
        return None

    path = current_app.config.get("ACCOUNTS_GEOIP_DB_PATH")
    if path:
        try:
            cc = _mmdb_country(path, ip)
        except Exception:
            # Not the IP in the message, it is personal data.
            current_app.logger.exception(
                "Cannot read the GeoIP database from ACCOUNTS_GEOIP_DB_PATH=%r, "
                "falling back to iptocc.",
                path,
            )
            cc = country_code(ip)
    else:
        cc = country_code(ip)

    # "EU" is a registry placeholder, not a country.
    return None if cc == "EU" else cc
