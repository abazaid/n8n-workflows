from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from xml.etree.ElementTree import Element, SubElement, ElementTree, Comment
from pathlib import Path
from datetime import datetime
from workflow_db import WorkflowDatabase

router = APIRouter()
db = WorkflowDatabase()

@router.get("/sitemap.xml", include_in_schema=False)
async def generate_sitemap():
    """
    ✅ توليد ملف Sitemap ديناميكي ومحسّن للـ SEO
    """
    try:
        # مسار ملف السايت ماب
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        sitemap_path = static_dir / "sitemap.xml"

        base_url = "https://workflowsbase.com"

        # إنشاء الجذر
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

                # 🔹 رابط الصفحة
                SubElement(url, "loc").text = f"{base_url}/api/workflows/{filename}"

                # 🔹 آخر تحديث بصيغة Google المعيارية
                if updated_at:
                    try:
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

                # 🔹 أضف الاسم كتـعليق (وليس كـTag)
                if name:
                    url.append(Comment(f" Workflow Name: {name} "))

        # ✅ 4. حفظ السايت ماب
        tree = ElementTree(urlset)
        tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)

        print(f"✅ Sitemap generated with {total} URLs: {sitemap_path}")
        return FileResponse(sitemap_path)

    except Exception as e:
        print(f"❌ Error generating sitemap: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating sitemap: {e}")
