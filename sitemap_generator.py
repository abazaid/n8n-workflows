from fastapi import APIRouter, Response
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
from workflow_db import WorkflowDatabase
from pathlib import Path
import json

router = APIRouter()
db = WorkflowDatabase()

@router.get("/sitemap.xml", response_class=Response)
async def sitemap():
    """توليد خريطة الموقع (sitemap.xml) ديناميكيًا لجميع الصفحات والـ workflows"""
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    base_url = "https://workflowsbase.com"

    def add_url(loc, changefreq="weekly", priority="0.8"):
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = loc
        SubElement(url, "changefreq").text = changefreq
        SubElement(url, "priority").text = priority

    # ✅ 1. الصفحة الرئيسية
    add_url(f"{base_url}/", changefreq="weekly", priority="1.0")

    # ✅ 2. صفحة البحث العامة
    add_url(f"{base_url}/api/workflows", changefreq="weekly", priority="0.8")

# ✅ 3. روابط جميع الـ Workflows من قاعدة البيانات
try:
    workflows, total = db.search_workflows(limit=5000, offset=0)
    for wf in workflows:
        filename = wf.get("filename")
        name = wf.get("name", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        updated_at = wf.get("updated_at") or wf.get("created_at")

        if filename:
            url = SubElement(urlset, "url")

            # 🔹 رابط الصفحة
            SubElement(url, "loc").text = f"{base_url}/api/workflows/{filename}"

            # 🔹 آخر تحديث بصيغة Google المعيارية (YYYY-MM-DD)
            if updated_at:
                try:
                    # لو التاريخ محفوظ كنص نحاول نحوله
                    date_str = str(updated_at).split(" ")[0]
                except:
                    date_str = datetime.utcnow().strftime("%Y-%m-%d")
            else:
                date_str = datetime.utcnow().strftime("%Y-%m-%d")

            SubElement(url, "lastmod").text = date_str

            # 🔹 تكرار التحديث
            SubElement(url, "changefreq").text = "monthly"

            # 🔹 أولوية متوسطة
            SubElement(url, "priority").text = "0.6"

            # 🔹 أضف الاسم كتـعليق (ليس عنصر) لتحسين القابلية للقراءة
            if name:
                url.append(Comment(f" Workflow Name: {name} "))

except Exception as e:
    print(f"⚠️ خطأ أثناء جلب الـ workflows: {e}")

    # ✅ 4. روابط جميع التصنيفات (Categories) تلقائيًا
    categories_file = Path("context/unique_categories.json")
    if categories_file.exists():
        try:
            with open(categories_file, "r", encoding="utf-8") as f:
                categories = json.load(f)
            for cat in categories:
                slug = cat.replace(" ", "-").lower()
                add_url(f"{base_url}/api/workflows/category/{slug}", changefreq="monthly", priority="0.5")
        except Exception as e:
            print(f"⚠️ خطأ أثناء قراءة التصنيفات: {e}")
    else:
        # fallback
        default_categories = ["ai-ml", "marketing", "ecommerce", "messaging"]
        for cat in default_categories:
            add_url(f"{base_url}/api/workflows/category/{cat}", changefreq="monthly", priority="0.5")

    # ✅ 5. توليد XML النهائي
    xml_str = tostring(urlset, encoding="utf-8", method="xml")
    return Response(content=xml_str, media_type="application/xml")
