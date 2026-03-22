import numpy as np
from sklearn.ensemble import RandomForestRegressor
from django.db.models import Avg, Count, Q
from accounts.models import User, UserReport
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_ai_recommended_doers(task):
    # 1. PRE-FILTERING (As before, to get candidates)
    qualified_doers = User.objects.filter(
        role='doer', is_active=True, approval_status='Accepted'
    ).filter(
        Q(doer_locations__pincode__place__district=task.district) | 
        Q(doer_skills__skill__category=task.category)
    ).distinct()

    if not qualified_doers.exists():
        return []

    # 2. FEATURE EXTRACTION (Turning Doers into Data Points)
    # We prepare the "X" (input features) for our Random Forest
    features = []
    doer_list = []
    
    # Get NLP scores first to use as a feature
    task_text = f"{task.title} {task.description}"
    doer_texts = [f"{getattr(d, 'bio', '')} {' '.join([s.skill.skill_name for s in d.doer_skills.all()])}" for d in qualified_doers]
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform([task_text] + doer_texts)
    nlp_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

    for index, doer in enumerate(qualified_doers):
        # Feature 1: Location Score (0-100)
        loc_score = 0
        if doer.doer_locations.filter(pincode=task.pincode).exists(): loc_score = 100
        elif doer.doer_locations.filter(pincode__place=task.place).exists(): loc_score = 60
        else: loc_score = 20

        # Feature 2: Skill Match (0 or 1)
        skill_match = 1 if doer.doer_skills.filter(skill=task.skill).exists() else 0

        # Feature 3: Rating
        stats = doer.reviews_received.aggregate(avg=Avg('rating'), count=Count('id'))
        rating = stats['avg'] or 0
        rev_count = stats['count'] or 0

        # Feature 4: Safety (Reports)
        reports = UserReport.objects.filter(reported_user=doer, is_resolved=False).count()

        # Append to our feature matrix [Location, Skill, Rating, Reviews, Reports, NLP]
        features.append([loc_score, skill_match, rating, rev_count, reports, nlp_scores[index]])
        doer_list.append({
            'user': doer,
            'avg_rating': rating,
            'review_count': rev_count
        })

    # 3. RANDOM FOREST PREDICTION
    X = np.array(features)
    
    # Initialize Random Forest Regressor
    # n_estimators=100 means it uses 100 decision trees
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # In a real system, you would .fit() on historical "Hired" data.
    # Here we use the priority logic to 'teach' the forest our weights initially.
    # Mock Target Y based on our business logic
    y = (X[:, 0] * 0.3) + (X[:, 1] * 40) + (X[:, 2] * 10) + (X[:, 3] * 2) - (X[:, 4] * 20) + (X[:, 5] * 50)
    
    rf_model.fit(X, y)
    
    # Predict scores
    final_scores = rf_model.predict(X)

    # 4. FINAL ASSEMBLY
    scored_list = []
    for i in range(len(doer_list)):
        # Normalize score to a 0-100 Match Percentage
        match_percentage = min(max(final_scores[i] / 2.5, 25), 99.5) 
        
        item = doer_list[i]
        item['score'] = final_scores[i]
        item['match_percentage'] = round(match_percentage, 1)
        scored_list.append(item)

    scored_list.sort(key=lambda x: x['score'], reverse=True)
    return scored_list[:3]