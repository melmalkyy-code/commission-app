"""Internationalisation — English (default) + Modern Arabic.

Usage:
    from src.i18n import t, is_rtl, q_label
    st.write(t("Total Sales"))
    selectbox(t("Quarter"), [1,2,3,4], format_func=q_label)
"""
from __future__ import annotations
import streamlit as st

_LANG_KEY = 'app_lang'

_Q_AR = {1: "الربع الأول", 2: "الربع الثاني", 3: "الربع الثالث", 4: "الربع الرابع"}

_AR: dict[str, str] = {
    # ── Navigation ────────────────────────────────────────────────────────────
    "Dashboard":            "الرئيسية",
    "Sales Input":          "تسجيل المبيعات",
    "KPI Calculation":      "تقييم الأداء",
    "Commission Report":    "تقرير العمولات",
    "Reports Center":       "مركز التقارير",
    "Settings":             "الإعدادات",
    "Audit Log":            "سجل التعديلات",
    "Active Period":        "الفترة الحالية",
    "Sign Out":             "تسجيل خروج",
    "Sign In":              "تسجيل الدخول",
    "Commission Manager":   "مدير العمولات",
    "Cloud database":       "قاعدة بيانات سحابية",
    "Local database (dev only)": "قاعدة بيانات محلية (تطوير فقط)",
    "Database unreachable": "تعذر الاتصال بقاعدة البيانات",
    "Changes will NOT be saved — database connection failed.": "لن يتم حفظ التغييرات — فشل الاتصال بقاعدة البيانات.",

    # ── General ───────────────────────────────────────────────────────────────
    "Year":             "العام",
    "Quarter":          "الربع",
    "Salesperson":      "مهندس المبيعات",
    "Salespersons":     "مهندسو المبيعات",
    "All Salespersons": "جميع مهندسي المبيعات",
    "Branch":           "الفرع",
    "Branches":         "الفروع",
    "Region":           "المنطقة",
    "Regions":          "المناطق",
    "By Region":        "حسب المنطقة",
    "Region Report":    "تقرير المنطقة",
    "Region Reports":   "تقارير المناطق",
    "No Region":        "بلا منطقة",
    "Tier":             "الشريحة",
    "Category":         "الفئة",
    "Categories":       "الفئات",
    "Target":           "المستهدف",
    "Sales":            "المبيعات",
    "Achievement":      "الإنجاز",
    "Commission":       "العمولة",
    "Total Sales":      "إجمالي المبيعات",
    "Total Target":     "المستهدف",
    "Base Commission":  "العمولة الأساسية",
    "Final Commission": "العمولة النهائية",
    "KPI Score":        "درجة الأداء",
    "KPI Multiplier":   "مضاعف الأداء",
    "On Target":        "حقق المستهدف",
    "Target Achieved":  "حقق المستهدف",
    "Locked":           "مقفل",
    "Open":             "مفتوح",
    "Active":           "نشط",
    "Inactive":         "غير نشط",
    "Name":             "الاسم",
    "Save":             "حفظ",
    "Delete":           "حذف",
    "Saved.":           "تم الحفظ.",
    "All":              "الكل",
    "Staff":            "عدد المهندسين",
    "Notes":            "ملاحظات",
    "User":             "المستخدم",
    "Time":             "الوقت",
    "Action":           "الإجراء",
    "Source":           "المصدر",
    "Metric":           "المؤشر",
    "Actual":           "الفعلي",
    "Rate":             "المعدل",
    "Sort":             "الترتيب",
    "Unlimited":        "غير محدود",
    "SAR (thousands)":  "ريال (بالآلاف)",
    "No data for this period.": "لا توجد بيانات لهذه الفترة.",

    # ── Dashboard ─────────────────────────────────────────────────────────────
    "Commission Dashboard":        "ملخص العمولات",
    "Company":                     "الشركة",
    "By Branch":                   "حسب الفرع",
    "By Region":                   "حسب المنطقة",
    "By Salesperson":              "حسب مهندس المبيعات",
    "Target vs Actual Sales":      "المبيعات الفعلية مقابل المستهدف",
    "Achievement Ranking":         "ترتيب الإنجاز",
    "Top Performers":              "الأفضل أداءً",
    "Sales Mix by Category":       "المبيعات حسب الفئة",
    "Salesperson Drilldown":       "تفاصيل مهندس المبيعات",
    "Select salesperson":          "اختر مهندس المبيعات",
    "Company Summary":             "ملخص الشركة",
    "Sales Trend by Salesperson":  "اتجاه المبيعات",
    "Sales Growth":                "نمو المبيعات",
    "Comm. Growth":                "نمو العمولة",
    "Achievement %":               "نسبة الإنجاز",
    "KPI Mult.":                   "مضاعف الأداء",
    "Final Comm.":                 "العمولة النهائية",
    "Base Comm.":                  "العمولة الأساسية",
    "Ach.":                        "الإنجاز",
    "Calculating...":              "جارٍ الحساب...",
    "Computing commissions...":    "جارٍ حساب العمولات...",
    "Loading data...":             "جارٍ تحميل البيانات...",
    "Growth QoQ":                  "النمو ربع السنوي",
    "Comparing {current} against {prev}. Growth is calculated as (Current − Previous) / Previous × 100.":
        "مقارنة {current} بـ {prev}. النمو = (الحالي - السابق) / السابق × 100.",
    "No data recorded for {prev_label} — enter sales for that quarter first.":
        "لا توجد بيانات لـ {prev_label} — أدخل المبيعات لذلك الربع أولاً.",

    # ── Sales Input ───────────────────────────────────────────────────────────
    "Enter actual sales amounts (SAR) for each salesperson":
        "أدخل المبيعات الفعلية (بالريال) لكل مهندس مبيعات",
    "Enter actual sales amounts (SAR) for each salesperson:":
        "أدخل المبيعات الفعلية (بالريال) لكل مهندس مبيعات:",
    "Changes are saved automatically as you edit each cell.":
        "يتم الحفظ تلقائياً عند التعديل.",
    "Changes saved":                "تم الحفظ",
    "Save All Changes":             "حفظ جميع التغييرات",
    "Saved all sales records for Q{quarter} {year}.":
        "تم حفظ جميع سجلات المبيعات للربع {quarter} {year}.",
    "Live Commission Preview":      "معاينة مباشرة للعمولة",
    "This quarter is locked. Contact your manager to unlock it in Settings.":
        "هذا الربع مقفل. تواصل مع مديرك لفتحه من الإعدادات.",
    "No active salespersons found. Please add salespersons in Settings first.":
        "لا يوجد مهندسو مبيعات نشطون. يُرجى إضافتهم من الإعدادات.",
    "No active categories found. Please configure categories in Settings first.":
        "لا توجد فئات نشطة. يُرجى إضافتها من الإعدادات.",
    "Import from Excel / Download Template":  "استيراد من إكسل / تحميل القالب",
    "Download Import Template":               "تحميل قالب الاستيراد",
    "Upload filled template:":                "رفع القالب المعبأ:",
    "Imported {count} records.":              "تم استيراد {count} سجل.",

    # ── KPI ───────────────────────────────────────────────────────────────────
    "Enter manual KPI scores (0–100) and review results":
        "أدخل درجات التقييم يدوياً وراجع النتائج",
    "KPI Scores — auto-calculated items are locked (grey); manual items are editable.":
        "درجات التقييم — المحسوبة تلقائياً مقفلة (بالرمادي)، واليدوية قابلة للتعديل.",
    "Scores are entered as raw values and calculated against each item's Max Score. Example: score 42 with Max 50 → 84 % of that item's weight.":
        "تُدخل الدرجات كقيم أولية وتُحسب كنسبة من الدرجة القصوى. مثال: 42 من 50 = 84% من وزن العنصر.",
    "KPI weights total {total_weight:.1f}% (should be 100%). Fix in Settings > KPI Settings.":
        "إجمالي الأوزان {total_weight:.1f}% (يجب أن يكون 100%). يمكن التعديل من الإعدادات.",
    "Auto-calculated from category achievement %. Read-only.":
        "محسوب تلقائياً من نسبة إنجاز الفئة. للقراءة فقط.",
    "Bonus pts":           "نقاط إضافية",
    "Penalty pts":         "نقاط خصم",
    "KPI changes saved":   "تم حفظ التقييم",
    "Save KPI Scores":     "حفظ درجات التقييم",
    "KPI scores saved.":   "تم حفظ درجات التقييم.",
    "KPI Results Preview": "معاينة نتائج الأداء",
    "Weighted Score":      "الدرجة المرجحة",
    "Bonus":               "المكافأة",
    "Penalty":             "الخصم",
    "Final KPI Score":     "درجة الأداء النهائية",
    "Detailed Item Breakdown (per salesperson)": "تفصيل العناصر (لكل مهندس مبيعات)",
    "KPI Item":    "عنصر الأداء",
    "Weight %":    "الوزن %",
    "Raw Score":   "الدرجة الخام",
    "Normalized":  "الدرجة المعيارية",
    "Contribution":"المساهمة",
    "KPI Breakdown":   "تفصيل مؤشرات الأداء",
    "KPI Score Breakdown": "تفصيل درجة مؤشرات الأداء",
    "No KPI items configured.": "لا توجد عناصر أداء معرّفة.",
    "Rule":            "القاعدة",
    "Score":           "الدرجة",
    "Achieved %":      "نسبة الإنجاز %",
    "Weighted Points": "النقاط المرجحة",
    "Auto":            "تلقائي",
    "Manual":          "يدوي",
    "Bonus / Penalty": "مكافأة / خصم",

    # ── Commission Report ─────────────────────────────────────────────────────
    "Base Commission × KPI Multiplier = Final Commission":
        "العمولة الأساسية × مضاعف الأداء = العمولة النهائية",
    "Company Level":      "مستوى الشركة",
    "Branch Level":       "مستوى الفرع",
    "Salesperson Level":  "مستوى مهندس المبيعات",
    "Branch Drilldown":   "تفاصيل الفرع",
    "Select Branch":      "اختر الفرع",
    "Select Salesperson": "اختر مهندس المبيعات",
    "No commission data available for this period.":
        "لا توجد بيانات عمولات لهذه الفترة.",
    "Actual Sales": "المبيعات الفعلية",
    "Bracket":      "الشريحة",
    "BASE COMMISSION":  "العمولة الأساسية",
    "KPI MULTIPLIER":   "مضاعف الأداء",
    "FINAL COMMISSION": "العمولة النهائية",

    # ── Reports Center ────────────────────────────────────────────────────────
    "Download commission reports at company, branch, and salesperson level":
        "حمّل تقارير العمولات للشركة، الفرع، ومهندس المبيعات",
    "Company Report":                "تقرير الشركة",
    "Company-Wide Report":           "تقرير الشركة الشامل",
    "Region Report":                 "تقرير المنطقة",
    "Region Reports":                "تقارير المناطق",
    "Select region to download":     "اختر المنطقة للتحميل",
    "Branch Reports":                "تقارير الفروع",
    "Salesperson Reports":           "تقارير مهندسي المبيعات",
    "Includes: Company Summary, All Salespersons, By Branch, Category Breakdown":
        "يشمل: ملخص الشركة، جميع مهندسي المبيعات، الفروع، وتفصيل الفئات",
    "Download Company Excel (4 sheets)": "تحميل إكسل الشركة (4 أوراق)",
    "Download Excel":                "تحميل إكسل",
    "Download PDF":                  "تحميل PDF",
    "Branch Report":                 "تقرير الفرع",
    "Salesperson Report":            "تقرير مهندس المبيعات",
    "Select Branch for Report":      "اختر الفرع للتقرير",
    "Select Salesperson for Report": "اختر مهندس المبيعات للتقرير",
    "Select branch to download":     "اختر الفرع للتحميل",
    "Download {branch} — Excel":     "تحميل {branch} — إكسل",
    "Download All Branches (one file)": "تحميل جميع الفروع (ملف واحد)",
    "No commission data for this period.":
        "لا توجد بيانات عمولات لهذه الفترة.",
    "All Salespersons Quick View":   "نظرة سريعة على جميع مهندسي المبيعات",

    # ── Settings ─────────────────────────────────────────────────────────────
    "Settings & Configuration": "الإعدادات",
    "Manage all system settings, targets, and commission rules":
        "إدارة الإعدادات، المستهدفات، وقواعد العمولات",
    "Access denied. Settings are only available to administrators.":
        "غير مصرح بالوصول. الإعدادات متاحة للمسؤولين فقط.",
    "View-only access: you can view dashboards and download reports, but cannot edit data or open this page.":
        "وصول للعرض فقط: يمكنك عرض لوحات المعلومات وتنزيل التقارير، لكن لا يمكنك تعديل البيانات أو فتح هذه الصفحة.",
    "Branding":              "هوية الشركة",
    "Company Branding":      "هوية الشركة",
    "Company Name":          "اسم الشركة",
    "Website":               "الموقع الإلكتروني",
    "Phone":                 "الهاتف",
    "Primary Color":         "اللون الأساسي",
    "Accent Color":          "اللون الثانوي",
    "Report Header":         "ترويسة التقرير",
    "Report Footer":         "تذييل التقرير",
    "PDF Watermark (optional)": "علامة مائية (اختياري)",
    "Save Branding":         "حفظ هوية الشركة",
    "Company Logo":          "شعار الشركة",
    "Remove Logo":           "حذف الشعار",
    "Upload logo (PNG or JPG, max 500 KB)":
        "رفع الشعار (PNG أو JPG، أقصاه 500 كيلوبايت)",
    "File too large — keep it under 500 KB.":
        "الملف كبير — يجب أن يكون أقل من 500 كيلوبايت.",
    "Logo saved.":           "تم حفظ الشعار.",
    "Add New Branch":        "إضافة فرع جديد",
    "Branch Name *":         "اسم الفرع *",
    "Region":                "المنطقة",
    "Add Branch":            "إضافة الفرع",
    "Target Tiers":          "شرائح المستهدفات",
    "Salesperson Target Tiers": "شرائح المستهدفات",
    "Add New Tier":          "إضافة شريحة جديدة",
    "Tier Name *":           "اسم الشريحة *",
    "Description":           "الوصف",
    "**Category Targets (SAR):**": "**مستهدفات الفئات (بالريال):**",
    "Add Tier":              "إضافة الشريحة",
    "Product / Service Categories": "فئات المنتجات والخدمات",
    "Add New Category":      "إضافة فئة جديدة",
    "Category Name *":       "اسم الفئة *",
    "Display Order":         "الترتيب",
    "Add Category":          "إضافة الفئة",
    "Order":                 "الترتيب",
    "In Target":             "في المستهدف",
    "In Commission":         "في العمولة",
    "In KPI":                "في الأداء",
    "Save Changes":          "حفظ التغييرات",
    "Categories saved.":     "تم حفظ الفئات.",
    "Category Commission Brackets": "شرائح العمولات",
    "Comm. Brackets":        "شرائح العمولات",
    "Select Category":       "اختر الفئة",
    "Calculation Method":    "طريقة الحساب",
    "Save Method":           "حفظ الطريقة",
    "Method saved.":         "تم حفظ الطريقة.",
    "From (SAR)":            "من (ريال)",
    "To (SAR)":              "إلى (ريال)",
    "Rate %":                "النسبة %",
    "Unlimited upper range (last bracket)": "نطاق غير محدود (آخر شريحة)",
    "Add Bracket":           "إضافة شريحة",
    "Save Brackets":         "حفظ الشرائح",
    "Brackets saved.":       "تم حفظ الشرائح.",
    "No brackets yet for this category. Add one below.":
        "لا توجد شرائح لهذه الفئة. أضف واحدة أدناه.",
    "No active categories. Add categories first.":
        "لا توجد فئات نشطة. أضف فئات أولاً.",
    "No categories yet. Use '＋ Add New Category' above to get started.":
        "لا توجد فئات. استخدم '＋ إضافة فئة جديدة' أعلاه للبدء.",
    "KPI Settings":          "إعدادات الأداء",
    "KPI Items & Weights":   "عناصر الأداء والأوزان",
    "Add New KPI Item":      "إضافة عنصر أداء جديد",
    "Name *":                "الاسم *",
    "Max Score":             "الدرجة القصوى",
    "Sort Order":            "الترتيب",
    "Add KPI Item":          "إضافة العنصر",
    "Save KPI Items":        "حفظ عناصر الأداء",
    "KPI items saved.":      "تم حفظ عناصر الأداء.",
    "Delete a KPI item":     "حذف عنصر أداء",
    "-- select --":          "-- اختر --",
    "Auto-Score from Category Achievement %":
        "الدرجة التلقائية من نسبة إنجاز الفئة",
    "Link a KPI item to a sales category — score is computed automatically from Actual / Target x 100 (capped at 100). Linked items do NOT appear in the manual KPI entry table.":
        "اربط عنصر الأداء بفئة مبيعات — يُحسب التقييم تلقائياً من الفعلي / المستهدف × 100.",
    "Manual - Enter Score":  "يدوي - أدخل الدرجة",
    "Save Category Links":   "حفظ ربط الفئات",
    "Category links saved.": "تم حفظ ربط الفئات.",
    "Active KPI weights total {total_wt:.1f}% (should be 100%).":
        "إجمالي الأوزان النشطة {total_wt:.1f}% (يجب أن يكون 100%).",
    "KPI Multiplier Rules":  "قواعد مضاعف الأداء",
    "Add New Multiplier Rule": "إضافة قاعدة مضاعف جديدة",
    "Score From":            "الدرجة من",
    "Score To":              "الدرجة إلى",
    "Multiplier":            "المضاعف",
    "Unlimited (no upper bound)": "غير محدود (بلا حد أعلى)",
    "Add Rule":              "إضافة القاعدة",
    "Save Multiplier Rules": "حفظ قواعد المضاعف",
    "Multiplier rules saved.": "تم حفظ قواعد المضاعف.",
    "Delete a rule":         "حذف قاعدة",
    "Delete selected rule":  "حذف القاعدة المحددة",
    "Periods":               "الفترات",
    "Period Settings":       "إعدادات الفترات",
    "Create Period":         "إنشاء فترة",
    "Set as Current":        "تعيين كحالية",
    "Set as current.":       "تم التعيين كحالية.",
    "Unlocked.":             "تم فتح القفل.",
    "Locked.":               "تم القفل.",
    "Users":                 "المستخدمون",
    "App Users":             "مستخدمو التطبيق",
    "Only admins can manage users.":
        "المسؤولون فقط يمكنهم إدارة المستخدمين.",
    "Add New User":          "إضافة مستخدم جديد",
    "Username *":            "اسم المستخدم *",
    "Full Name":             "الاسم الكامل",
    "Password *":            "كلمة المرور *",
    "Confirm Password *":    "تأكيد كلمة المرور *",
    "Role":                  "الدور",
    "Create User":           "إنشاء مستخدم",
    "Username and password are required.":
        "اسم المستخدم وكلمة المرور مطلوبان.",
    "Passwords do not match.": "كلمتا المرور غير متطابقتين.",
    "New Password":          "كلمة المرور الجديدة",
    "Confirm New Password":  "تأكيد كلمة المرور الجديدة",
    "Leave blank to keep current": "اتركه فارغاً للإبقاء على الحالية",
    "Cannot delete your own account.": "لا يمكن حذف حسابك الخاص.",
    "Add New Salesperson":   "إضافة مهندس مبيعات جديد",
    "Full Name *":           "الاسم الكامل *",
    "Branch *":              "الفرع *",
    "Target Tier *":         "الشريحة المستهدفة *",
    "Email":                 "البريد الإلكتروني",
    "Add Salesperson":       "إضافة مهندس المبيعات",
    "Target Tier":           "الشريحة المستهدفة",

    # ── Audit Log ────────────────────────────────────────────────────────────
    "Complete trail of all data changes and user actions":
        "سجل كامل لجميع التغييرات والإجراءات",
    "Filter by Action":      "تصفية حسب الإجراء",
    "Filter by Entity":      "تصفية حسب العنصر",
    "Max Records":           "الحد الأقصى للسجلات",
    "Old Value":             "القيمة القديمة",
    "New Value":             "القيمة الجديدة",
    "Download Audit Log (Excel)":
        "تحميل سجل التعديلات (إكسل)",
    "No audit records match the current filters.":
        "لا توجد سجلات تطابق الفلاتر الحالية.",

    # ── Login ────────────────────────────────────────────────────────────────
    "Commission Manager — Sign In":     "مدير العمولات — تسجيل الدخول",
    "Please enter both username and password.":
        "يُرجى إدخال اسم المستخدم وكلمة المرور.",
    "Invalid username or password.":    "اسم المستخدم أو كلمة المرور غير صحيح.",
    "Username":  "اسم المستخدم",
    "Password":  "كلمة المرور",
    "Enter username": "أدخل اسم المستخدم",
    "Enter password": "أدخل كلمة المرور",

    # ── Report Download UI ───────────────────────────────────────────────────
    "Report Language":     "لغة التقرير",
    "Language":            "اللغة",
    "Format":              "الصيغة",
    "Download Report":     "تحميل التقرير",
    "Report Options":      "خيارات التقرير",
    "English":             "English",
    "Arabic":              "عربي",
    "PDF is English only. Choose Excel for Arabic output.":
        "ملف PDF باللغة الإنجليزية فقط. اختر إكسل للحصول على مخرجات عربية.",

    # ── Excel / Report Headers ───────────────────────────────────────────────
    "Value":                     "القيمة",
    "TOTAL":                     "الإجمالي",
    "COMPANY TOTAL":             "إجمالي الشركة",
    "By Category":               "حسب الفئة",
    "Category Breakdown":        "تفصيل الفئات",
    "Commission Summary":        "ملخص العمولة",
    "QoQ vs":                    "مقارنة بـ",
    "QoQ Comparison":            "مقارنة ربع السنوية",
    "FINAL COMMISSION GROWTH":   "نمو العمولة النهائية",
    "Total Sales (SAR)":         "إجمالي المبيعات (ريال)",
    "Total Target (SAR)":        "المستهدف (ريال)",
    "Base Commission (SAR)":     "العمولة الأساسية (ريال)",
    "Final Commission (SAR)":    "العمولة النهائية (ريال)",
    "Total Salespersons":        "إجمالي مهندسي المبيعات",
    "Achieved Target":           "حقق المستهدف",
    "Rate %":                    "النسبة %",
    "KPI x":                     "مضاعف الأداء",
    "Ach. Δ pp":                 "فرق نقاط الإنجاز",

    # ── Misc ─────────────────────────────────────────────────────────────────
    "That name already exists - choose a different one.":
        "هذا الاسم موجود مسبقاً - اختر اسماً مختلفاً.",
    "records found":  "سجل",
}


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_lang() -> str:
    return st.session_state.get(_LANG_KEY, 'en')


def is_rtl() -> bool:
    return get_lang() == 'ar'


def t(text: str) -> str:
    """Return Arabic translation if language is Arabic, else return text unchanged."""
    if get_lang() != 'ar':
        return text
    return _AR.get(text, text)


def tl(text: str, lang: str) -> str:
    """Translate with an explicit language parameter — for report generators
    that must produce a specific language regardless of the current UI language."""
    if lang != 'ar':
        return text
    return _AR.get(text, text)


def q_label(q: int) -> str:
    """Format a quarter number for display (e.g. 2 → 'Q2' or 'الربع الثاني')."""
    if get_lang() != 'ar':
        return f"Q{q}"
    return _Q_AR.get(q, f"Q{q}")


def lang_switcher() -> None:
    """Render the language toggle in the sidebar."""
    lang = get_lang()
    st.sidebar.markdown(
        "<div style='text-align:center;font-size:10px;text-transform:uppercase;"
        "letter-spacing:.1em;color:rgba(255,255,255,0.4);margin:10px 0 6px'>"
        "Language / اللغة</div>",
        unsafe_allow_html=True,
    )
    col_en, col_ar = st.sidebar.columns(2)
    with col_en:
        if st.button(
            "EN", key="_lang_en",
            type="primary" if lang == 'en' else "secondary",
            use_container_width=True,
        ):
            st.session_state[_LANG_KEY] = 'en'
            st.rerun()
    with col_ar:
        if st.button(
            "عربي", key="_lang_ar",
            type="primary" if lang == 'ar' else "secondary",
            use_container_width=True,
        ):
            st.session_state[_LANG_KEY] = 'ar'
            st.rerun()
    st.sidebar.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)
