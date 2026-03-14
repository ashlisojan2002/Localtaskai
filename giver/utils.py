from django.db.models import Avg
from accounts.models import User, UserReport
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_ai_recommended_doers(task):
    # 1. HARD FILTER: Must have the skill, be active, and be Accepted (Verified)
    qualified_doers = User.objects.filter(
        role='doer',
        is_active=True,
        approval_status='Accepted',
        doer_skills__skill=task.skill
    ).distinct()

    if not qualified_doers:
        return []

    # 2. NLP PREPARATION: Compare Task text with Doer profiles
    task_text = f"{task.title} {task.description}"
    # We combine the Doer's bio and any additional info for text matching
    # Replace the crashing line (around line 21) with this:
    doer_texts = [f"{getattr(d, 'bio', '')}" for d in qualified_doers]
    
    # Calculate Text Similarity Scores
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform([task_text] + doer_texts)
    # Compare the first item (task) with all other items (doers)
    nlp_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

    scored_list = []

    # 3. COMBINED SCORING
    for index, doer in enumerate(qualified_doers):
        score = 0
        
        # A. Location Score (Same as your current logic)
        work_areas = doer.doer_locations.all()
        if work_areas.filter(pincode=task.pincode).exists():
            score += 50
        elif work_areas.filter(pincode__place=task.place).exists():
            score += 30
        elif work_areas.filter(pincode__place__district=task.district).exists():
            score += 10

        # B. Reputation Score
        stats = doer.reviews_received.aggregate(avg=Avg('rating'))
        avg_rating = stats['avg'] or 0
        score += (avg_rating * 40) 

        # C. Safety Penalty
        reports = UserReport.objects.filter(reported_user=doer, is_resolved=False).count()
        score -= (reports * 20) 

        # D. NLP BOOST (The "Real AI" part)
        # We multiply by 100 to make the 0.0-1.0 similarity scale meaningful against other points
        nlp_boost = nlp_scores[index] * 100
        score += nlp_boost

        scored_list.append({
            'user': doer,
            'score': score,
            'avg_rating': avg_rating,
            'match_percentage': round((nlp_scores[index] * 100), 1) # For the UI
        })

    # Sort by highest combined score
    scored_list.sort(key=lambda x: x['score'], reverse=True)
    return scored_list[:3]