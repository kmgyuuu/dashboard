import folium
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from streamlit_folium import folium_static
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from matplotlib import font_manager
import warnings
warnings.filterwarnings('ignore')

font_path = './Nanum_Gothic/NanumGothic-Regular.ttf'
prop = font_manager.FontProperties(fname=font_path)

# Load data
df1 = pd.read_csv('./git_data/grid_병합.csv')
df2 = pd.read_csv('./git_data/grid_4.csv')
review = pd.read_csv('./git_data/지점별_월별_리뷰수.csv')
emotion = pd.read_csv('./git_data/지점별_감정분석.csv')
keyword = pd.read_csv('./git_data/지점별_키워드.csv')
best_grid = gpd.read_file('./git_data/nlsp_020001001.shp' ,encoding='utf8')
wordcloud_df = pd.read_csv('./git_data/지점별_워드클라우드.csv')
dong = pd.read_csv("./git_data/좌표_동일업체.csv")

emotion = emotion[['지점명','label']]
emotion = emotion.groupby('지점명').agg({'label': ['count', 'sum']})
emotion = emotion.assign(ratio=emotion[('label', 'sum')] / emotion[('label', 'count')])

best_grid.geometry = best_grid.geometry.to_crs("EPSG:4326")
best_grid.drop(columns=['lbl','val'],inplace=True)
best_grid = best_grid[(best_grid['gid'] == '다바9314') | (best_grid['gid'] == '다바9415') | (best_grid['gid'] == '다바8817') | (best_grid['gid'] == '다바8915')]

# Define function to show home screen
def show_home():
    st.title('대전 맥도날드 입지 분석')
    st.write(' ')
    m = folium.Map(location=[36.3504, 127.3845], zoom_start=12)
    for index, row in best_grid.iterrows():
        folium.GeoJson(row['geometry']).add_to(m)
    for idx, row in dong.iterrows():
        folium.Marker([row['위도'], row['경도']], popup=row['Name']).add_to(m)
    st_folium(m,height=575,width=725)

    col1,col2 = st.columns([2,2])
    with col1 :
        st.dataframe(df1)
    with col2 :
        st.dataframe(df2)



# Define function to show data for selected species
def show_species_data():
    select_species = st.sidebar.selectbox(
        '지점을 골라주세요.',
        ['유성DT점', '카이스트점', '가수원DT점', '가장DT점', '한남대DT점', '세이브존_대전점', '센트럴DT점', '대전터미널점', '부사DT점', '신탄진DT점', '유천DT점', '목원대점']
    )

    st.title(select_species+'   감정 분석')
    st.write('데이터')
    # 리뷰 월별
    review_data = review[review['지점명'] == select_species]
    review_counts = review_data['YearMonth'].value_counts().sort_index()
    lineplot = px.line(x=review_counts.index.astype(str),
                        y=review_counts.values,
                        markers=True,
                        title= select_species+" 년월별 데이터 개수",
                        labels={'x': 'YearMonth', 'y': 'Data Count'})
    
    # 감정분석
    emotion_score = emotion[emotion.index == select_species]['ratio'].values[0] * 100
    emotionplot = go.Figure(go.Indicator(mode="gauge+number",
                                        value=emotion_score,
                                        domain={'x': [0, 1], 'y': [0, 1]},
                                        title={'text': select_species+" 소비자 점수"},
                                        gauge={'axis': {'range': [None, 100]}}))

    ### 긍정 워드클라우드
    ture_df = wordcloud_df[wordcloud_df['지점명'] == select_species]
    positive_data = ture_df[ture_df['label'] == 1]
    positive_data['content'] = positive_data['content'].str.replace('\n', '')
    
    words = positive_data['content'].explode()
    words_df = pd.DataFrame({'word': words})
    words_df['count'] = words_df['word'].str.len()

    words_df = words_df.query('count >= 2')
    words_count_df = words_df.groupby('word', as_index=False).count().sort_values('count', ascending=False)
    #words_count_df = words_count_df.head(50)

    wordcloud1 = WordCloud(font_path = font_path, width=400, height=400, background_color='white').generate_from_frequencies(dict(zip(words_count_df['word'], words_count_df['count'])))
    
    fig1 = plt.figure(figsize=(5, 5))
    plt.title(select_species+"의 부정 단어 워드클라우드", fontproperties=prop)
    plt.imshow(wordcloud1, interpolation='bilinear')
    plt.axis('off')

    ### 부정 워드클라우드
    false_df = wordcloud_df[wordcloud_df['지점명'] == select_species]
    ngeative_data = false_df[false_df['label'] == 0]
    ngeative_data['content'] = ngeative_data['content'].str.replace('\n', '')
    idx =ngeative_data[ngeative_data['content'].str.contains("좋|역시|맛있")].index
    ngeative_data = ngeative_data.drop(idx)

    contents = ngeative_data['content'].explode()
    words_df1 = pd.DataFrame({'content': contents})
    words_df1['count'] = words_df1['content'].str.len()
    words_df1 = words_df1.query('count > 4')
    #words_df1 = words_df1.head(50)

    wordcloud2 = WordCloud(font_path = font_path, width=400, height=400, background_color='white').generate(' '.join(words_df1['content']))

    fig2 = plt.figure(figsize=(5, 5))
    plt.title(select_species+"의 부정 단어 워드클라우드", fontproperties=prop)
    plt.imshow(wordcloud2, interpolation='bilinear')
    plt.axis('off')

    # 키워드 분석
    keyword_data = keyword[keyword['지점명'] == select_species]
    keyword_data = keyword_data.sort_values(by='count', ascending=False).head(8)
    kewyword_plot = px.line_polar(keyword_data, r='count', theta='better', line_close=True)
    kewyword_plot.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showline=False,
                showticklabels=False,
            ),
        ),
        showlegend=False,
        title=select_species+" - Top 8 Features",
    )


    kewyword_plot.update_traces(text=keyword_data['count'], textposition='top center', textfont=dict(size=12))

    st.dataframe(review_data,use_container_width=True)
    st.plotly_chart(lineplot)
    st.plotly_chart(kewyword_plot)

    col3,col4 = st.columns([2,2])
    with col3 :
        st.pyplot(fig1)
    with col4 :
        st.pyplot(fig2)
    
    st.plotly_chart(emotionplot)

# Main app
def main():
    st.sidebar.title('못난이 삼남매')
    app_mode = st.sidebar.radio("분석 페이지를 골라주세요.", ["입지 분석", "감성 분석"])

    if app_mode == "입지 분석":
        show_home()
    elif app_mode == "감성 분석":
        show_species_data()

if __name__ == "__main__":
    main()
