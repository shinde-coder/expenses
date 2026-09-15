from catalogs.models import Category, CategoryType, MasterValue, PaymentMethod, SubCategory

EXPENSE_CATEGORIES = [
    ("Housing", "home", "#1F4E78", [
        "Rent/EMI", "Maintenance", "Repairs",
    ]),
    ("Utilities", "bolt", "#F4B942", [
        "Electricity", "Water", "Gas", "Internet", "Mobile", "Mobile Recharge",
    ]),
    ("Groceries", "shopping_cart", "#E67E22", [
        "Supermarket", "Vegetables/Fruits", "Meat/Dairy", "Snacks", "Kirana",
    ]),
    ("Transportation", "directions_car", "#2980B9", [
        "Fuel", "Public Transport", "Cab/Taxi", "Vehicle Maintenance",
    ]),
    ("Food & Dining", "restaurant", "#C0392B", [
        "Restaurants", "Food Delivery",
    ]),
    ("Healthcare", "local_hospital", "#27AE60", [
        "Doctor Visits", "Medicines", "Insurance",
    ]),
    ("Education", "school", "#8E44AD", [
        "School Fees", "Tuition", "Books & Supplies",
    ]),
    ("Personal Care", "spa", "#D35400", [
        "Salon", "Clothing", "Toiletries",
    ]),
    ("Entertainment", "movie", "#16A085", [
        "Movies", "Subscriptions", "Outings",
    ]),
    ("Kids", "child_care", "#E91E63", [
        "Daycare", "Toys", "Activities",
    ]),
    ("Miscellaneous", "more_horiz", "#7F8C8D", [
        "Gifts", "Donations", "Other",
    ]),
]

SAVING_CATEGORIES = [
    ("Savings & Investment", "savings", "#2ECC71", [
        "SIP/Mutual Funds", "Fixed Deposit", "Emergency Fund",
    ]),
]

INCOME_CATEGORIES = [
    ("Salary", "payments", "#1ABC9C", []),
    ("Business", "storefront", "#3498DB", []),
    ("Freelance", "work", "#9B59B6", []),
    ("Interest", "trending_up", "#27AE60", []),
    ("Cashback", "redeem", "#F39C12", []),
    ("Other Income", "add_card", "#95A5A6", []),
]

PAYMENT_METHODS = [
    ("Cash", "payments"),
    ("Debit Card", "credit_card"),
    ("Credit Card", "credit_score"),
    ("UPI", "qr_code"),
    ("Net Banking", "account_balance"),
    ("Cheque", "receipt_long"),
]

MASTER_VALUES = {
    "transaction_type": [
        ("EXPENSE", "Expense", "south_west", "#E11D48", 0, {
            "prompt": "Money out", "sign": "-", "budget": True,
        }),
        ("INCOME", "Income", "trending_up", "#059669", 1, {
            "prompt": "Money in", "sign": "+", "budget": False,
        }),
        ("SAVING", "Saving", "savings", "#4F46E5", 2, {
            "prompt": "Money saved", "sign": "-", "budget": False,
        }),
    ],
    "relationship": [
        ("SELF", "Me", "person", "#0F766E", 0, {"aliases": ["me"], "assignable": False}),
        ("DAD", "Dad", "face", "#0284C7", 1, {"aliases": ["dad", "father"]}),
        ("MOM", "Mom", "face_3", "#DB2777", 2, {"aliases": ["mom", "mother"]}),
        ("SPOUSE", "Spouse", "favorite", "#E11D48", 3, {"aliases": ["wife", "husband", "spouse"]}),
        ("CHILD", "Child", "child_care", "#D97706", 4, {"aliases": ["child", "kid", "son", "daughter"]}),
        ("OTHER", "Other", "group", "#64748B", 5, {"aliases": ["other"]}),
    ],
    "frequency": [
        ("DAILY", "Daily", "today", "#0284C7", 0, {
            "unit": "day", "count": 1, "applies_to": ["recurring", "bill"],
        }),
        ("WEEKLY", "Weekly", "view_week", "#0D9488", 1, {
            "unit": "week", "count": 1, "applies_to": ["recurring", "bill"],
        }),
        ("MONTHLY", "Monthly", "calendar_month", "#4F46E5", 2, {
            "unit": "month", "count": 1, "applies_to": ["recurring", "bill"],
        }),
        ("QUARTERLY", "Quarterly", "date_range", "#7C3AED", 3, {
            "unit": "month", "count": 3, "applies_to": ["recurring", "bill"],
        }),
        ("YEARLY", "Yearly", "calendar_today", "#D97706", 4, {
            "unit": "year", "count": 1, "applies_to": ["recurring", "bill"],
        }),
        ("ONCE", "One time", "event", "#64748B", 5, {
            "unit": "once", "count": 0, "applies_to": ["bill"],
        }),
    ],
    "report_type": [
        ("monthly", "Monthly", "summarize", "#0284C7", 0, {}),
        ("category", "Category", "category", "#7C3AED", 1, {}),
        ("member", "Family member", "groups", "#DB2777", 2, {}),
        ("payment-method", "Payment method", "payments", "#059669", 3, {}),
        ("budget", "Budget", "pie_chart", "#D97706", 4, {}),
        ("income-vs-expense", "Income vs expense", "swap_vert", "#E11D48", 5, {}),
        ("savings", "Savings", "savings", "#4F46E5", 6, {}),
    ],
    "analytics_period": [
        ("weekly", "Week", "view_week", "#0284C7", 0, {"unit": "week"}),
        ("monthly", "Month", "calendar_month", "#4F46E5", 1, {"unit": "month"}),
        ("yearly", "Year", "calendar_today", "#D97706", 2, {"unit": "year"}),
    ],
    "export_format": [
        ("csv", "CSV", "table_chart", "#0284C7", 0, {}),
        ("xlsx", "Excel", "grid_on", "#059669", 1, {}),
        ("pdf", "PDF", "picture_as_pdf", "#E11D48", 2, {}),
    ],
    "member_role": [
        ("OWNER", "Owner", "verified", "#0F766E", 0, {}),
        ("EDITOR", "Editor", "edit", "#0284C7", 1, {}),
        ("VIEWER", "Viewer", "visibility", "#64748B", 2, {}),
    ],
    "goal_status": [
        ("ACTIVE", "Active", "flag", "#4F46E5", 0, {}),
        ("ACHIEVED", "Achieved", "verified", "#059669", 1, {}),
        ("ABANDONED", "Abandoned", "flag", "#64748B", 2, {}),
    ],
}


def seed_system_catalogs():
    created = {
        "categories": 0,
        "subcategories": 0,
        "payment_methods": 0,
        "masters": 0,
    }

    def upsert_group(items, category_type):
        for name, icon, color, subs in items:
            category, was_created = Category.objects.get_or_create(
                family=None,
                name=name,
                type=category_type,
                defaults={"icon": icon, "color": color, "is_active": True},
            )
            if was_created:
                created["categories"] += 1
            for sub_name in subs:
                _, sub_created = SubCategory.objects.get_or_create(
                    category=category,
                    name=sub_name,
                    defaults={"family": None, "is_active": True},
                )
                if sub_created:
                    created["subcategories"] += 1

    upsert_group(EXPENSE_CATEGORIES, CategoryType.EXPENSE)
    upsert_group(SAVING_CATEGORIES, CategoryType.SAVING)
    upsert_group(INCOME_CATEGORIES, CategoryType.INCOME)

    for name, icon in PAYMENT_METHODS:
        _, was_created = PaymentMethod.objects.get_or_create(
            family=None,
            name=name,
            defaults={"icon": icon, "is_active": True},
        )
        if was_created:
            created["payment_methods"] += 1

    for group, rows in MASTER_VALUES.items():
        for code, label, icon, color, sort_order, extra in rows:
            obj, was_created = MasterValue.objects.get_or_create(
                group=group,
                code=code,
                defaults={
                    "label": label,
                    "icon": icon,
                    "color": color,
                    "sort_order": sort_order,
                    "extra": extra,
                    "is_active": True,
                },
            )
            if was_created:
                created["masters"] += 1
            elif extra:
                merged = {**(obj.extra or {}), **extra}
                if merged != (obj.extra or {}):
                    obj.extra = merged
                    obj.save(update_fields=["extra", "updated_at"])
    return created
