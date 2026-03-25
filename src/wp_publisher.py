"""
WordPress Publisher — A2S SEO Bot
מתחבר ל-WordPress דרך JWT ומעלה מאמרים כטיוטות
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")


def get_jwt_token():
    """מקבל JWT token מ-WordPress"""
    response = requests.post(
        f"{WP_URL}/wp-json/jwt-auth/v1/token",
        json={"username": WP_USERNAME, "password": WP_PASSWORD}
    )
    data = response.json()
    if "token" not in data:
        raise Exception(f"JWT Error: {data}")
    return data["token"]


def get_or_create_category(token, category_name):
    """מוצא קטגוריה קיימת או יוצר חדשה"""
    headers = {"Authorization": f"Bearer {token}"}

    # חיפוש קטגוריה קיימת
    response = requests.get(
        f"{WP_URL}/wp-json/wp/v2/categories",
        params={"search": category_name},
        headers=headers
    )
    categories = response.json()
    if categories:
        return categories[0]["id"]

    # יצירת קטגוריה חדשה
    response = requests.post(
        f"{WP_URL}/wp-json/wp/v2/categories",
        json={"name": category_name},
        headers=headers
    )
    return response.json()["id"]


def upload_image(token, image_path, image_title):
    """מעלה תמונה ל-WordPress Media Library"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
    }
    with open(image_path, "rb") as img:
        response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers=headers,
            files={"file": (os.path.basename(image_path), img, "image/jpeg")},
            data={"title": image_title, "alt_text": image_title}
        )
    if response.status_code not in (200, 201):
        print(f"Image upload failed: {response.text}")
        return None
    return response.json()["id"]


def publish_post(title, content, meta_description, slug, category_name,
                 tags=None, featured_image_path=None, status="draft"):
    """
    מעלה מאמר ל-WordPress

    Args:
        title: כותרת המאמר
        content: תוכן HTML של המאמר
        meta_description: תיאור ל-SEO (All in One SEO)
        slug: כתובת URL של המאמר
        category_name: שם הקטגוריה
        tags: רשימת תגיות
        featured_image_path: נתיב לתמונה ראשית (אופציונלי)
        status: "draft" או "publish"

    Returns:
        dict עם פרטי הפוסט שנוצר
    """
    print(f"\n[A2S SEO Bot] מעלה מאמר: {title}")

    # 1. קבלת token
    token = get_jwt_token()
    print("  JWT token: OK")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. קטגוריה
    category_id = get_or_create_category(token, category_name)
    print(f"  קטגוריה: {category_name} (ID: {category_id})")

    # 3. תגיות
    tag_ids = []
    if tags:
        for tag_name in tags:
            response = requests.post(
                f"{WP_URL}/wp-json/wp/v2/tags",
                json={"name": tag_name},
                headers=headers
            )
            if response.status_code in (200, 201):
                tag_ids.append(response.json()["id"])

    # 4. תמונה ראשית
    featured_image_id = None
    if featured_image_path and os.path.exists(featured_image_path):
        featured_image_id = upload_image(token, featured_image_path, title)
        print(f"  תמונה: הועלתה (ID: {featured_image_id})")

    # 5. יצירת הפוסט
    post_data = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": status,
        "categories": [category_id],
        "tags": tag_ids,
        "meta": {
            "_aioseo_description": meta_description,
            "_aioseo_title": title,
        }
    }

    if featured_image_id:
        post_data["featured_media"] = featured_image_id

    response = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        json=post_data,
        headers=headers
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Post creation failed: {response.text}")

    post = response.json()
    print(f"  מאמר נוצר בהצלחה!")
    print(f"  סטטוס: {status}")
    print(f"  קישור: {post.get('link', '')}")
    print(f"  ID: {post['id']}")

    return post


if __name__ == "__main__":
    # בדיקת חיבור
    try:
        token = get_jwt_token()
        print(f"חיבור ל-WordPress: תקין")
        print(f"אתר: {WP_URL}")
    except Exception as e:
        print(f"שגיאה: {e}")
