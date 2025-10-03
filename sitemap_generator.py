from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from xml.etree.ElementTree import Element, SubElement, ElementTree, Comment
from pathlib import Path
from datetime import datetime
from workflow_db import WorkflowDatabase
import re

router = APIRouter()
db = WorkflowDatabase()

@router.get("/sitemap.xml", include_in_schema=False)
async def generate_sitemap():
    """
    ✅ توليد ملف Sitemap ديناميكي ومتوافق 100٪ مع معايير Google
    """
    try:
        # 📁 إعداد المسارات
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        sitemap_path = static_dir / "sitemap.xml"

        base_url = "https://workflowsbase.com"

        # 🧱 إنشاء جذر ملف XML
        urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

        # ✅ 1. الصفحة الرئيسية
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = f"{base_url}/"
        SubElement(url, "changefreq").text = "weekly"
        SubElement(url, "priority").text = "1.0"

        # ✅ 2. صفحة البحث / API الرئيسية
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = f"{base_url}/api/workflows"
        SubElement(url, "changefreq").text = "weekly"
        SubElement(url, "priority").text = "0.8"

        # ✅ 3. روابط جميع الـ Workflows من قاعدة البيانات
        workflows, total = db.search_workflows(limit=5000, offset=0)
        for wf in workflows:
            filename = wf.get("filename")
            name = wf.get("name", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            updated_at = wf.get("updated_at") or wf.get("created_at")

            if filename:
                url = SubElement(urlset, "url")

                # 🔗 رابط الصفحة
                SubElement(url, "loc").text = f"{base_url}/api/workflows/{filename}"

                # 🕓 آخر تعديل بصيغة YYYY-MM-DD
                if updated_at:
                    try:
                        date_str = str(updated_at).split(" ")[0]
                    except:
                        date_str = datetime.utcnow().strftime("%Y-%m-%d")
                else:
                    date_str = datetime.utcnow().strftime("%Y-%m-%d")

                SubElement(url, "lastmod").text = date_str

                # 🔁 التكرار
                SubElement(url, "changefreq").text = "monthly"
                SubElement(url, "priority").text = "0.6"

                # 🏷️ أضف الاسم كتـعليق فقط
                if name:
                    url.append(Comment(f" Workflow Name: {name} "))

        # 💾 حفظ الملف
        tree = ElementTree(urlset)
        tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)

        # 🧹 تنظيف أي أكواد HTML غريبة تُضاف تلقائيًا مثل <div ... />
        with open(sitemap_path, "r", encoding="utf-8") as f:
            content = f.read()

        # إزالة أي div أو script تم حقنه تلقائيًا
        content = re.sub(r'<div[^>]*\/>', '', content)
        content = re.sub(r'<script[^>]*>.*?<\/script>', '', content, flags=re.DOTALL)

        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Sitemap generated successfully with {total} URLs: {sitemap_path}")

        # 🔁 إرجاع الملف مع Content-Type الصحيح
        return FileResponse(sitemap_path, media_type="application/xml")

    except Exception as e:
        print(f"❌ Error generating sitemap: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating sitemap: {e}")
