from odoo.tests import common


class TestWebReadGroup(common.TransactionCase):
    """Test the 'length' logic of web_read_group_unity, groups logic
    are tested in test_formatted_read_group"""

    maxDiff = None

    def test_limit_offset_performance(self):
        Model = self.env["test_read_group.aggregate"]
        Model.create(
            [
                {"key": 1, "value": 1},
                {"key": 1, "value": 2},
                {"key": 1, "value": 3},
                {"key": 2, "value": 4},
                {"key": 2},
                {"key": 2, "value": 5},
                {},
                {"value": 6},
            ],
        )

        # warmup
        Model.web_read_group_unity([], groupby=["key"], aggregates=["value:sum"])

        # One query for read_group because limit is reached
        with self.assertQueryCount(1):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    limit=4,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        # One _read_group with the limit and other without to get the length
        with self.assertQueryCount(2):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    limit=2,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                    ],
                    "length": 3,
                },
            )

        # One _read_group/query because limit is reached
        with self.assertQueryCount(1):
            self.assertEqual(
                Model.web_read_group_unity(
                    [], groupby=["key"], aggregates=["value:sum"], offset=1
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        with self.assertQueryCount(2):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    offset=1,
                    limit=2,
                    forced_order=[{"name": "key", "asc": False}],
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                    ],
                    "length": 3,
                },
            )

    def test_unfolded_group_limit(self):
        Model = self.env["test_read_group.aggregate"]
        records = Model.create(
            [
                {"key": 1, "value": 1},
                {"key": 1, "value": 2},
                {"key": 1, "value": 3},
                {"key": 2, "value": 4},
                {"key": 2},
                {"key": 2, "value": 5},
                {},
                {"value": 6},
            ],
        )

        read_spec = {
            "key": {},
            "value": {},
        }
        key1_read_records = records[:3].web_read(read_spec)
        key2_read_records = records[3:6].web_read(read_spec)

        # Warmup ormcache
        Model.web_read_group_unity(
            [],
            groupby=["key"],
            aggregates=["value:sum"],
            unfolded_group_limit=2,
            unfold_read_specification=read_spec,
        )

        self.env.invalidate_all()

        # One query formatted_read_group
        # One query for multi searching (get records for each column)
        # One query to read records
        with self.assertQueryCount(3):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=2,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__records": key1_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": key2_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        self.env.invalidate_all()

        # One query formatted_read_group
        # One query for multi searching (get records for each column)
        # One query to read records
        with self.assertQueryCount(3):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=2,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__records": key1_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": key2_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        self.env.invalidate_all()

        # One query formatted_read_group
        # One query to get the number of group (because limit is reached)
        # One query for multi searching (get records for each column)
        # One query to read records
        with self.assertQueryCount(4):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    offset=1,
                    limit=1,
                    unfolded_group_limit=2,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": key2_read_records,
                        },
                    ],
                    "length": 3,
                },
            )

    def test_unfolded_specific_groups(self):
        Model = self.env["test_read_group.aggregate"]
        partner_1, partner_2 = self.env["res.partner"].create(
            [
                {"name": "P1"},
                {"name": "P2"},
            ],
        )
        records = Model.create(
            [
                {"partner_id": partner_1.id, "key": 1, "value": 1},
                {"partner_id": partner_1.id, "key": 1, "value": 2},
                {"partner_id": partner_1.id, "key": 1, "value": 3},
                {"partner_id": partner_2.id, "key": 1, "value": 4},
                {"partner_id": partner_2.id, "key": 2},
                {"partner_id": partner_2.id, "value": 5},
                {},
                {"value": 6},
            ],
        )

        read_spec = {
            "key": {},
            "value": {},
            "partner_id": {"fields": {"display_name": {}}},
        }

        # Warmup ormcache
        Model.web_read_group_unity(
            [],
            groupby=["partner_id", "key"],
            aggregates=["value:sum"],
        )

        # Scenario: list view groupby ['partner_id', 'key'] - no group opened by default
        self.env.invalidate_all()

        # One query for the _read_group
        # One query to read the display_name of partner_id
        with self.assertQueryCount(2):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["partner_id", "key"],
                    aggregates=["value:sum"],
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("partner_id", "=", partner_1.id)],
                            "partner_id": (partner_1.id, "P1"),
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                        {
                            "__extra_domain": [("partner_id", "=", partner_2.id)],
                            "partner_id": (partner_2.id, "P2"),
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("partner_id", "=", False)],
                            "partner_id": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        # Scenario:
        # Client opened manually several groups and reload the view (add a filter / change of views / ...).
        # Simulate that DEFAULT_GROUP_LIMIT is 2.
        opening_info = [
            {
                "value": partner_1.id,
                "folded": False,  # open the partner group (partner=P1)
                "limit": 2,
                "offset": 0,
                "extra_domain": [],
                "groups": [
                    {
                        "value": 1,
                        "folded": False,  # open the subgroup (key=1)
                        "limit": 2,
                        "offset": 2,  # next page of records
                        "extra_domain": [],
                    },
                ],
            },
            {
                "value": partner_2.id,
                "folded": False,  # open the partner group (partner=P2)
                "limit": 2,
                "offset": 2,  # next page of subgroups
                "extra_domain": [],
                "groups": [
                    {
                        "value": False,
                        "folded": False,  # open the subgroup (key=False)
                        "limit": 2,
                        "offset": 0,
                        "extra_domain": [],
                    },
                ],
            },
            {
                "value": False,
                "folded": True,
            },
        ]
        read_record_2 = records[2].web_read(read_spec)
        read_record_5 = records[5].web_read(read_spec)

        self.env.invalidate_all()

        # One query for the main _read_group
        # One query for the to open subgroup partner=P1
        # One query for the to open subgroup partner=P2
        # One query to fetch all records
        # One query to read fields of test_read_group.aggregate fields
        # One query to read display_name of partner
        with self.assertQueryCount(6):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["partner_id", "key"],
                    aggregates=["value:sum"],
                    opening_info=opening_info,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("partner_id", "=", partner_1.id)],
                            "partner_id": (partner_1.id, "P1"),
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__groups": {
                                "groups": [
                                    {
                                        "__extra_domain": [("key", "=", 1)],
                                        "key": 1,
                                        "__count": 3,
                                        "value:sum": 1 + 2 + 3,
                                        "__records": read_record_2,
                                    },
                                ],
                                "length": 1,
                            },
                        },
                        {
                            "__extra_domain": [("partner_id", "=", partner_2.id)],
                            "partner_id": (partner_2.id, "P2"),
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__groups": {
                                "groups": [
                                    {
                                        "key": False,
                                        "__extra_domain": [("key", "=", False)],
                                        "value:sum": 5,
                                        "__count": 1,
                                        "__records": read_record_5,
                                    }
                                ],
                                "length": 3,
                            },
                        },
                        {
                            "__extra_domain": [("partner_id", "=", False)],
                            "partner_id": False,
                            "__count": 2,
                            "value:sum": 6,
                            # Group no opened since it is an Falsy value
                        },
                    ],
                    "length": 3,
                },
            )

    def test_auto_unfolded(self):
        """Test unfolded groups when no __fold exists"""
        Model = self.env["test_read_group.aggregate"]
        partner_1, partner_2 = self.env["res.partner"].create(
            [
                {"name": "P1"},
                {"name": "P2"},
            ],
        )
        records = Model.create(
            [
                {"partner_id": partner_1.id, "key": 1, "value": 1},
                {"partner_id": partner_1.id, "key": 1, "value": 2},
                {"partner_id": partner_1.id, "key": 1, "value": 3},
                {"partner_id": partner_2.id, "key": 1, "value": 4},
                {"partner_id": partner_2.id, "key": 2},
                {"partner_id": partner_2.id, "value": 5},
                {},
                {"value": 6},
            ],
        )

        read_spec = {
            "key": {},
            "value": {},
            "partner_id": {"fields": {"display_name": {}}},
        }

        # Warmup ormcache
        Model.web_read_group_unity(
            [],
            groupby=["partner_id"],
            aggregates=["value:sum"],
            unfolded_group_limit=10,
            unfold_read_specification=read_spec,
        )
        self.env.invalidate_all()

        # Scenario: groupby many2one (no __fold informatoion) on a kanban view

        # One query for the _read_group
        # One query to read the display_name of partner_id
        # One query to get all records
        # One query to read all records opened
        with self.assertQueryCount(4):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["partner_id"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=10,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("partner_id", "=", partner_1.id)],
                            "partner_id": (partner_1.id, "P1"),
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__records": records[:3].web_read(read_spec),
                        },
                        {
                            "__extra_domain": [("partner_id", "=", partner_2.id)],
                            "partner_id": (partner_2.id, "P2"),
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": records[3:6].web_read(read_spec),
                        },
                        {
                            "__extra_domain": [("partner_id", "=", False)],
                            "partner_id": False,
                            "__count": 2,
                            "value:sum": 6,
                            # No __records since we don't opened False relational value by default
                        },
                    ],
                    "length": 3,
                },
            )

        self.env.invalidate_all()

        # Scenario: list view with expaned="1", auto opened the first level of groupby

        # One query for the _read_group
        # One query to read the display_name of partner_id
        # One query to open subgroups partner_1 (not batched - hard to do)
        # One query to open subgroups partner_2
        with self.assertQueryCount(4):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["partner_id", "key"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=10,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("partner_id", "=", partner_1.id)],
                            "partner_id": (partner_1.id, "P1"),
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__groups": {
                                "groups": [
                                    {
                                        "__extra_domain": [("key", "=", 1)],
                                        "key": 1,
                                        "__count": 3,
                                        "value:sum": 1 + 2 + 3,
                                    },
                                ],
                                "length": 1,
                            },
                        },
                        {
                            "__extra_domain": [("partner_id", "=", partner_2.id)],
                            "partner_id": (partner_2.id, "P2"),
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__groups": {
                                "groups": [
                                    {
                                        "__extra_domain": [("key", "=", 1)],
                                        "key": 1,
                                        "__count": 1,
                                        "value:sum": 4,
                                    },
                                    {
                                        "__extra_domain": [("key", "=", 2)],
                                        "key": 2,
                                        "__count": 1,
                                        "value:sum": False,
                                    },
                                    {
                                        "__extra_domain": [("key", "=", False)],
                                        "key": False,
                                        "__count": 1,
                                        "value:sum": 5,
                                    },
                                ],
                                "length": 3,
                            },
                        },
                        {
                            "__extra_domain": [("partner_id", "=", False)],
                            "partner_id": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

    def test_extra_domain_records(self):
        # Scenario: Open a kanban view, select an part of the records with the progress bar.
        pass

    def test_auto_fold_info(self):
        """Test when __fold exists in subgroup"""
        order_1, order_2, order_3, order_4 = self.env["test_read_group.order"].create(
            [
                {"name": "O1", "fold": False},
                {"name": "O2", "fold": True},
                {"name": "O3 empty", "fold": False},
                {"name": "O4 empty", "fold": True},
            ]
        )
        Line = self.env["test_read_group.order.line"].with_context(
            read_group_expand=True
        )
        records = Line.create(
            [
                {"order_expand_id": order_1.id, "value": 1},
                {"order_expand_id": order_2.id, "value": 2},
                {"order_expand_id": order_2.id, "value": 2},
                {"order_expand_id": False, "value": 3},
            ]
        )

        read_spec = {"value": {}}

        # warmup ormcache
        Line.web_read_group_unity(
            [],
            groupby=["order_expand_id"],
            aggregates=["value:sum"],
            unfolded_group_limit=10,
            unfold_read_specification=read_spec,
        )

        self.env.invalidate_all()

        # Scenario: kanban view where fold information is in the comodel

        # One query for the _read_group
        # One query for the _read_group_expand_full of order_expand_id
        # One query to read the display_name/fold of order_expand_id
        # One query to get all records
        # One query to read all records opened
        with self.assertQueryCount(5):
            self.assertEqual(  # No group_expand limit reached directly
                Line.web_read_group_unity(
                    [],
                    groupby=["order_expand_id"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=10,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "order_expand_id": (order_1.id, "O1"),
                            "__extra_domain": [("order_expand_id", "=", order_1.id)],
                            "value:sum": 1,
                            "__count": 1,
                            "__records": records[0].web_read(read_spec),
                        },
                        {
                            "order_expand_id": (order_2.id, "O2"),
                            "__extra_domain": [("order_expand_id", "=", order_2.id)],
                            "value:sum": 4,
                            "__count": 2,
                        },
                        {
                            "order_expand_id": (order_3.id, "O3 empty"),
                            "__extra_domain": [("order_expand_id", "=", order_3.id)],
                            "value:sum": False,
                            "__count": 0,
                            "__records": [],
                        },
                        {
                            "order_expand_id": (order_4.id, "O4 empty"),
                            "__extra_domain": [("order_expand_id", "=", order_4.id)],
                            "value:sum": False,
                            "__count": 0,
                        },
                        {
                            "order_expand_id": False,
                            "__extra_domain": [("order_expand_id", "=", False)],
                            "value:sum": 3,
                            "__count": 1,
                        },
                    ],
                    "length": 5,
                },
            )

        # Scenario: view list where fold information is in the comodel

        self.env.invalidate_all()

        # One query for the _read_group
        # One query for the _read_group_expand_full of order_expand_id
        # One query to read the display_name/fold of order_expand_id
        # One query to get all records
        # One query to read all records opened
        with self.assertQueryCount(5):
            self.assertEqual(  # No group_expand limit reached directly
                Line.web_read_group_unity(
                    [],
                    groupby=["order_expand_id", "value"],
                    aggregates=[],
                    unfolded_group_limit=10,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "order_expand_id": (order_1.id, "O1"),
                            "__extra_domain": [("order_expand_id", "=", order_1.id)],
                            "__count": 1,
                            "__groups": {
                                "groups": [
                                    {
                                        "value": 1,
                                        "__extra_domain": [("value", "=", 1)],
                                        "__count": 1,
                                        # Shouldn't be unfold
                                    },
                                ],
                                "length": 1,
                            },
                        },
                        {
                            "order_expand_id": (order_2.id, "O2"),
                            "__extra_domain": [("order_expand_id", "=", order_2.id)],
                            "__count": 2,
                        },
                        {
                            "order_expand_id": (order_3.id, "O3 empty"),
                            "__extra_domain": [("order_expand_id", "=", order_3.id)],
                            "__count": 0,
                            "__groups": {
                                "groups": [],
                                "length": 0,
                            },
                        },
                        {
                            "order_expand_id": (order_4.id, "O4 empty"),
                            "__extra_domain": [("order_expand_id", "=", order_4.id)],
                            "__count": 0,
                        },
                        {
                            "order_expand_id": False,
                            "__extra_domain": [("order_expand_id", "=", False)],
                            "__count": 1,
                        },
                    ],
                    "length": 5,
                },
            )

    def test_forced_order(self):
        pass
        # TODO: test with forced_order

    def test_read_extra_info_groupby_value(self):
        pass
        # TODO: test with groupby_read_specification
