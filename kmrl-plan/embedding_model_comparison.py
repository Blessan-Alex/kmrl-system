from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def calculate_similarity(model, sentences, model_name):
    """Calculate cosine similarity for given sentences using specified model"""
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print(f"{'='*60}")
    
    # Generate embeddings
    embeddings = model.encode(sentences)
    
    # Calculate cosine similarity
    similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    print(f"Text 1: {sentences[0]}")
    print(f"Text 2: {sentences[1]}")
    print(f"Cosine Similarity: {similarity_score:.6f}")
    
    return similarity_score

# Load all three models
print("Loading models...")
vyakyarth_model = SentenceTransformer("krutrim-ai-labs/vyakyarth")
minilm_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
multilingual_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# Test cases for comparison
test_cases = [
    {
        "name": "Malayalam - Similar Meaning",
        "sentences": [
            "മലയാളം ഭാഷാ പഠനം",
            "മലയാളം ഭാഷാ അധ്യയനം"
        ]
    },
    {
        "name": "Malayalam - Different Topics", 
        "sentences": [
            "കമ്പ്യൂട്ടർ സയൻസ് പഠനം",
            "ഗണിത ശാസ്ത്രം പഠനം"
        ]
    },
    {
        "name": "English - Similar Meaning",
        "sentences": [
            "Machine learning is fascinating",
            "Artificial intelligence is interesting"
        ]
    },
    {
        "name": "English - Different Topics",
        "sentences": [
            "Computer science programming",
            "Mathematics and statistics"
        ]
    },
    {
        "name": "Cross-lingual (Malayalam-English)",
        "sentences": [
            "മലയാളം ഭാഷാ പഠനം",
            "Malayalam language learning"
        ]
    },
    {
        "name": "Same Text (Should be 1.0)",
        "sentences": [
            "രാത്രി സേവന സുരക്ഷാ സർക്കുലർ",
            "രാത്രി സേവന സുരക്ഷാ സർക്കുലർ"
        ]
    }
]

# Results storage
results = []

# Test each case with all three models
for test_case in test_cases:
    print(f"\n{'#'*80}")
    print(f"TEST CASE: {test_case['name']}")
    print(f"{'#'*80}")
    
    # Test with Vyakyarth model
    vyakyarth_score = calculate_similarity(
        vyakyarth_model, 
        test_case['sentences'], 
        "Vyakyarth (Krutrim)"
    )
    
    # Test with MiniLM model
    minilm_score = calculate_similarity(
        minilm_model, 
        test_case['sentences'], 
        "all-MiniLM-L6-v2"
    )
    
    # Test with Multilingual MPNet model
    multilingual_score = calculate_similarity(
        multilingual_model, 
        test_case['sentences'], 
        "paraphrase-multilingual-mpnet-base-v2"
    )
    
    # Store results
    results.append({
        'test_case': test_case['name'],
        'vyakyarth_score': vyakyarth_score,
        'minilm_score': minilm_score,
        'multilingual_score': multilingual_score,
        'vyakyarth_minilm_diff': abs(vyakyarth_score - minilm_score),
        'vyakyarth_multilingual_diff': abs(vyakyarth_score - multilingual_score),
        'minilm_multilingual_diff': abs(minilm_score - multilingual_score)
    })

# Summary comparison
print(f"\n{'='*100}")
print("SUMMARY COMPARISON - ALL THREE MODELS")
print(f"{'='*100}")
print(f"{'Test Case':<30} {'Vyakyarth':<12} {'MiniLM':<12} {'Multilingual':<12} {'V-M Diff':<12} {'V-Multi Diff':<12}")
print("-" * 100)

for result in results:
    print(f"{result['test_case']:<30} {result['vyakyarth_score']:<12.6f} {result['minilm_score']:<12.6f} {result['multilingual_score']:<12.6f} {result['vyakyarth_minilm_diff']:<12.6f} {result['vyakyarth_multilingual_diff']:<12.6f}")

# Calculate average differences
avg_vyakyarth_minilm_diff = np.mean([r['vyakyarth_minilm_diff'] for r in results])
avg_vyakyarth_multilingual_diff = np.mean([r['vyakyarth_multilingual_diff'] for r in results])
avg_minilm_multilingual_diff = np.mean([r['minilm_multilingual_diff'] for r in results])

print(f"\nAverage differences between models:")
print(f"Vyakyarth vs MiniLM: {avg_vyakyarth_minilm_diff:.6f}")
print(f"Vyakyarth vs Multilingual: {avg_vyakyarth_multilingual_diff:.6f}")
print(f"MiniLM vs Multilingual: {avg_minilm_multilingual_diff:.6f}")

# Model performance analysis
vyakyarth_avg = np.mean([r['vyakyarth_score'] for r in results])
minilm_avg = np.mean([r['minilm_score'] for r in results])
multilingual_avg = np.mean([r['multilingual_score'] for r in results])

print(f"\nAverage similarity scores:")
print(f"Vyakyarth (Krutrim): {vyakyarth_avg:.6f}")
print(f"all-MiniLM-L6-v2: {minilm_avg:.6f}")
print(f"paraphrase-multilingual-mpnet-base-v2: {multilingual_avg:.6f}")

# Find the best performing model
models = {
    'Vyakyarth': vyakyarth_avg,
    'MiniLM': minilm_avg,
    'Multilingual': multilingual_avg
}

best_model = max(models, key=models.get)
best_score = models[best_model]

print(f"\n🏆 BEST PERFORMING MODEL: {best_model} with {best_score:.6f} average similarity")

# Calculate percentage differences
print(f"\nPercentage differences from best model:")
for model_name, score in models.items():
    if model_name != best_model:
        diff_percent = ((best_score - score) / best_score) * 100
        print(f"{model_name}: {diff_percent:.2f}% lower than {best_model}")

# Model ranking
sorted_models = sorted(models.items(), key=lambda x: x[1], reverse=True)
print(f"\nModel Ranking (by average similarity):")
for i, (model_name, score) in enumerate(sorted_models, 1):
    print(f"{i}. {model_name}: {score:.6f}")

