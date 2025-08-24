
# Personalized Content Recommendation Based on Spending and Mood Check-In
# Dependencies: pandas, openai (optional for smart match)

import pandas as pd
from datetime import datetime

# Sample user check-in input
user_checkin = {
    "mood": "anxious",
    "interest": ["money", "health"],
    "timestamp": datetime.utcnow().isoformat()
}

# Simulated user spending behavior
user_spending_flags = ["overspending_food", "delayed_rent"]

# Load curated content (can be a DB query instead of CSV)
content_df = pd.read_csv("curated_content.csv")  # Contains columns: id, title, tags, summary, url, etc.

# Simple matching function based on tags
def recommend_content(user_checkin, spending_flags, content_df):
    recommended = []

    for _, row in content_df.iterrows():
        tags = row["tags"].lower().split(",")
        if any(flag.replace("_", " ") in tags for flag in spending_flags) or            any(topic.lower() in tags for topic in user_checkin["interest"]):
            recommended.append({
                "title": row["title"],
                "summary": row["summary"],
                "url": row["url"],
                "why": f"Recommended based on your interest in {', '.join(user_checkin['interest'])} and spending behavior."
            })
    
    return recommended[:3]  # Return top 3 recommendations

# Sample run
recommendations = recommend_content(user_checkin, user_spending_flags, content_df)

# Print recommendations
for rec in recommendations:
    print(f"- {rec['title']}: {rec['summary']} ({rec['url']})\n{rec['why']}\n")
