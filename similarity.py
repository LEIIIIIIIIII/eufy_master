from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import re

class SimilarityMatcher:
    def __init__(self, solution_database):
        self.database = solution_database
        self.vectorizer = TfidfVectorizer()
        
    def preprocess_text(self, text):
        """预处理文本"""
        # 转为小写
        text = text.lower()
        # 移除特殊字符
        text = re.sub(r'[^\w\s]', '', text)
        # 中文分词
        words = jieba.cut(text)
        return " ".join(words)
    
    def find_similar_case(self, location, floor_plan, requirements):
        """查找最相似的案例"""
        # 将新案例转换为查询文本
        query = f"{location} {floor_plan} {requirements}"
        query = self.preprocess_text(query)
        
        # 准备所有历史案例
        historical_cases = []
        historical_texts = []
        
        for case in self.database['examples']:
            case_text = f"{case['location']} {case['floor_plan']} {case['requirements']}"
            case_text = self.preprocess_text(case_text)
            historical_texts.append(case_text)
            historical_cases.append(case)
        
        # 如果没有历史案例，返回None
        if not historical_texts:
            return None
            
        # 计算TF-IDF向量
        try:
            tfidf_matrix = self.vectorizer.fit_transform([query] + historical_texts)
            
            # 计算相似度
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            # 找到最相似的案例
            max_sim_idx = similarities[0].argmax()
            max_similarity = similarities[0][max_sim_idx]
            
            # 如果相似度超过阈值，返回该案例
            if max_similarity > 0.3:  # 可以调整阈值
                return historical_cases[max_sim_idx]
            
        except Exception as e:
            print(f"Similarity calculation error: {str(e)}")
            
        return None