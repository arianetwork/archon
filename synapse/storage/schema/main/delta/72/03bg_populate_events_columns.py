#
# This file is licensed under the Affero General Public License (AGPL) version 3.
#
# Copyright (C) 2023 New Vector, Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# See the GNU Affero General Public License for more details:
# <https://www.gnu.org/licenses/agpl-3.0.html>.
#
# Originally licensed under the Apache License, Version 2.0:
# <http://www.apache.org/licenses/LICENSE-2.0>.
#
# [This file includes modifications made by New Vector Limited]
#
#

import json

from synapse.storage.database import LoggingTransaction
from synapse.storage.engines import BaseDatabaseEngine


def run_create(cur: LoggingTransaction, database_engine: BaseDatabaseEngine) -> None:
    """Add a bg update to populate the `state_key` and `rejection_reason` columns of `events`"""

    # we know that any new events will have the columns populated (and that has been
    # the case since schema_version 68, so there is no chance of rolling back now).
    #
    # So, we only need to make sure that existing rows are updated. We read the
    # current min and max stream orderings, since that is guaranteed to include all
    # the events that were stored before the new columns were added.
    cur.execute("SELECT MIN(stream_ordering), MAX(stream_ordering) FROM events")
    row = cur.fetchone()
    assert row is not None
    (min_stream_ordering, max_stream_ordering) = row

    if min_stream_ordering is None:
        # no rows, nothing to do.
        return

    cur.execute(
        "INSERT into background_updates (ordering, update_name, progress_json)"
        " VALUES (7203, 'events_populate_state_key_rejections', ?)",
        (
            json.dumps(
                {
                    "min_stream_ordering_exclusive": min_stream_ordering - 1,
                    "max_stream_ordering_inclusive": max_stream_ordering,
                }
            ),
        ),
    )
