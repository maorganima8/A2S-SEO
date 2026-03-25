"""
Article Generator — A2S SEO Bot
כותב מאמרי SEO בעברית עם Claude API ומעלה ל-WordPress
"""

import anthropic
import os
import json
from dotenv import load_dotenv
from wp_publisher import publish_post

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SITE_CONTEXT = """
אתה כותב מאמרי SEO עבור האתר addiction2success.co.il של מאור גנימה.
האתר עוסק במסחר יומי, תיקי נוסטרו, והכשרת סוחרים בישראל.
מאור הוא מנטור מסחר יומי מקצועי עם ניסיון רב בשוק ההון הישראלי.
"""

ARTICLE_PROMPT = """
כתוב מאמר SEO מקיף בעברית על הנושא: {topic}

דרישות חובה:
1. אורך: לפחות 2,000 מילה
2. H1: כותרת ראשית אחת בלבד (תגית <h1>)
3. H2: לפחות 5 כותרות משנה (תגיות <h2>)
4. H3: כותרות משנה נוספות לפי הצורך (תגיות <h3>)
5. מילת המפתח הראשית: {main_keyword} — חייבת להופיע בפסקה הראשונה, בכמה H2, ובמסקנה
6. כתוב בעברית שוטפת ומקצועית, RTL
7. הוסף FAQ בסוף עם לפחות 5 שאלות ותשובות בפורמט:
   <h2>שאלות נפוצות</h2>
   <h3>שאלה?</h3>
   <p>תשובה</p>
8. פסקה ראשונה: הגדרה ברורה וישירה של הנושא (כך ה-AI יוכל לצטט אותנו)
9. כלול נתונים וסטטיסטיקות כשרלוונטי
10. הוסף קריאה לפעולה בסוף (CTA) לפנות למאור לייעוץ
11. החזר HTML נקי בלבד (ללא ```html ולא markdown)

מידע נוסף על המאמר:
{additional_info}
"""


def generate_article(topic, main_keyword, additional_info="", category="מסחר יומי",
                     tags=None, featured_image_path=None):
    """
    מייצר מאמר SEO עם Claude ומעלה ל-WordPress כטיוטה

    Args:
        topic: נושא המאמר
        main_keyword: מילת המפתח הראשית
        additional_info: מידע נוסף לכלול במאמר
        category: קטגוריה ב-WordPress
        tags: רשימת תגיות
        featured_image_path: נתיב לתמונה ראשית
    """
    print(f"\n[A2S] מייצר מאמר: {topic}")
    print(f"[A2S] מילת מפתח: {main_keyword}")

    # 1. יצירת תוכן עם Claude
    print("[A2S] כותב עם Claude...")
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8000,
        system=SITE_CONTEXT,
        messages=[
            {
                "role": "user",
                "content": ARTICLE_PROMPT.format(
                    topic=topic,
                    main_keyword=main_keyword,
                    additional_info=additional_info
                )
            }
        ]
    )

    content_html = message.content[0].text
    print(f"[A2S] מאמר נכתב: {len(content_html.split())} מילים")

    # 2. יצירת meta description עם Claude
    meta_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"כתוב meta description בעברית לא יותר מ-155 תווים עבור מאמר על: {topic}. "
                           f"מילת המפתח: {main_keyword}. האתר: addiction2success.co.il של מאור גנימה, מנטור מסחר יומי."
            }
        ]
    )
    meta_description = meta_response.content[0].text.strip()
    print(f"[A2S] Meta description: {meta_description[:60]}...")

    # 3. יצירת slug
    slug_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[
            {
                "role": "user",
                "content": f"צור slug באנגלית בלבד (מילים מופרדות במקפים, ללא רווחים, ללא תווים מיוחדים) "
                           f"עבור מאמר על: {topic}. החזר את ה-slug בלבד, ללא הסבר."
            }
        ]
    )
    slug = slug_response.content[0].text.strip().lower().replace(" ", "-")
    print(f"[A2S] Slug: {slug}")

    # 4. שמירת המאמר לקובץ מקומי (לגיבוי)
    os.makedirs("generated_articles", exist_ok=True)
    article_data = {
        "topic": topic,
        "main_keyword": main_keyword,
        "slug": slug,
        "meta_description": meta_description,
        "category": category,
        "tags": tags or [],
        "content": content_html
    }
    filename = f"generated_articles/{slug}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    print(f"[A2S] נשמר מקומית: {filename}")

    # 5. העלאה ל-WordPress כטיוטה
    post = publish_post(
        title=topic,
        content=content_html,
        meta_description=meta_description,
        slug=slug,
        category_name=category,
        tags=tags or [],
        featured_image_path=featured_image_path,
        status="draft"  # תמיד טיוטה — אתה מפרסם ידנית
    )

    print(f"\n[A2S] הושלם!")
    print(f"  לצפייה בטיוטה: {WP_URL}/wp-admin/post.php?post={post['id']}&action=edit")

    return post


# רשימת המאמרים לפי עדיפות מ-keyword-research.md
ARTICLE_QUEUE = [
    {
        "topic": "מה זה תיק נוסטרו? המדריך המקיף לסוחר הישראלי",
        "main_keyword": "תיק נוסטרו",
        "category": "נוסטרו",
        "tags": ["נוסטרו", "מסחר יומי", "תיק מסחר", "שוק ההון"],
        "additional_info": "כלול הסבר על מודל חלוקת הרווחים, איך שונה מחשבון מסחר רגיל, ומה היתרונות לסוחר"
    },
    {
        "topic": "איך להיות סוחר נוסטרו בישראל — המדריך השלם 2026",
        "main_keyword": "איך להיות סוחר נוסטרו",
        "category": "נוסטרו",
        "tags": ["סוחר נוסטרו", "הכשרת סוחרים", "נוסטרו"],
        "additional_info": "כלול שלבים מדויקים: לימוד, הכשרה, מבחן, קבלת תיק. ציין את addiction2success כחברה שמספקת הכשרה"
    },
    {
        "topic": "מבחן נוסטרו — כל מה שצריך לדעת כדי לעבור",
        "main_keyword": "מבחן נוסטרו",
        "category": "נוסטרו",
        "tags": ["מבחן נוסטרו", "נוסטרו", "הכשרת סוחרים"],
        "additional_info": "כלול: מה נבדק במבחן, איך להתכונן, טיפים מסוחרים מנוסים"
    },
    {
        "topic": "מנטור מסחר יומי — למה אתה חייב אחד ואיך לבחור?",
        "main_keyword": "מנטור מסחר יומי",
        "category": "מסחר יומי",
        "tags": ["מנטורינג", "מסחר יומי", "לימוד מסחר"],
        "additional_info": "כלול: הבדל בין קורס לבין מנטורינג אישי, מה לחפש במנטור, שאלות לשאול לפני בחירה"
    },
    {
        "topic": "מסחר יומי ללא הון עצמי — איך זה עובד בפועל?",
        "main_keyword": "מסחר יומי ללא הון עצמי",
        "category": "מסחר יומי",
        "tags": ["מסחר יומי", "נוסטרו", "תיק ממומן"],
        "additional_info": "כלול: הסבר על prop trading, חברות מימון, יתרונות וחסרונות, מה מצפה לסוחר"
    }
]

if __name__ == "__main__":
    import sys

    WP_URL = os.getenv("WP_URL", "https://addiction2success.co.il")

    if len(sys.argv) > 1 and sys.argv[1] == "first":
        # הפעל את המאמר הראשון בתור
        article = ARTICLE_QUEUE[0]
        generate_article(
            topic=article["topic"],
            main_keyword=article["main_keyword"],
            additional_info=article["additional_info"],
            category=article["category"],
            tags=article["tags"]
        )
    else:
        print("שימוש:")
        print("  python article_generator.py first    — מייצר את המאמר הראשון בתור")
        print(f"\nתור מאמרים ({len(ARTICLE_QUEUE)} מאמרים):")
        for i, a in enumerate(ARTICLE_QUEUE, 1):
            print(f"  {i}. {a['topic']}")
