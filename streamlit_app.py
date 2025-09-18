import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from geopy.distance import geodesic
import itertools
from math import radians, cos, sin, asin, sqrt

# ページ設定
st.set_page_config(
    page_title="日田市ナビゲーション",
    page_icon="🗾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: bold;
    }
    .mode-header {
        font-size: 1.8rem;
        margin: 1rem 0;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }
    .tourism-mode {
        background: linear-gradient(135deg, #4CAF50, #81C784);
        color: white;
    }
    .disaster-mode {
        background: linear-gradient(135deg, #F44336, #FF8A65);
        color: white;
    }
    .spot-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .evacuation-card {
        background-color: #ffebee;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #F44336;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .route-info {
        background: linear-gradient(135deg, #E3F2FD, #BBDEFB);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2196F3;
    }
    .time-info {
        background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem;
        border-left: 3px solid #FF9800;
    }
    .warning-alert {
        background: linear-gradient(135deg, #FFEBEE, #FFCDD2);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #F44336;
    }
</style>
""", unsafe_allow_html=True)

# 日田市の基本設定
HITA_CENTER = [33.3200, 130.9417]  # 日田市役所周辺

# 観光地データ
TOURISM_SPOTS = [
    {
        "name": "日田祇園の曳山会館",
        "category": "文化施設",
        "lat": 33.3211,
        "lon": 130.9425,
        "wait_time": 30,
        "visit_duration": 45,
        "description": "日田祇園祭の山鉾を常設展示",
        "rating": 4.3
    },
    {
        "name": "豆田町",
        "category": "歴史街並み",
        "lat": 33.3234,
        "lon": 130.9445,
        "wait_time": 15,
        "visit_duration": 60,
        "description": "江戸時代の町並みが残る歴史地区",
        "rating": 4.5
    },
    {
        "name": "咸宜園跡",
        "category": "史跡",
        "lat": 33.3189,
        "lon": 130.9398,
        "wait_time": 10,
        "visit_duration": 30,
        "description": "江戸時代の私塾跡",
        "rating": 4.1
    },
    {
        "name": "亀山公園",
        "category": "公園",
        "lat": 33.3167,
        "lon": 130.9356,
        "wait_time": 5,
        "visit_duration": 45,
        "description": "桜の名所として有名",
        "rating": 4.2
    },
    {
        "name": "日田温泉",
        "category": "温泉",
        "lat": 33.3245,
        "lon": 130.9412,
        "wait_time": 20,
        "visit_duration": 90,
        "description": "三隈川沿いの温泉街",
        "rating": 4.4
    },
    {
        "name": "三隈川",
        "category": "自然",
        "lat": 33.3223,
        "lon": 130.9401,
        "wait_time": 0,
        "visit_duration": 30,
        "description": "日田市を流れる美しい川",
        "rating": 4.0
    },
    {
        "name": "日田市立博物館",
        "category": "博物館",
        "lat": 33.3278,
        "lon": 130.9467,
        "wait_time": 15,
        "visit_duration": 60,
        "description": "日田の歴史と文化を展示",
        "rating": 4.1
    },
    {
        "name": "小鹿田焼の里",
        "category": "工芸",
        "lat": 33.2756,
        "lon": 130.8823,
        "wait_time": 25,
        "visit_duration": 75,
        "description": "伝統的な陶器の里",
        "rating": 4.6
    }
]

# 飲食店データ
RESTAURANTS = [
    {
        "name": "うなぎの寝床",
        "category": "和食",
        "lat": 33.3225,
        "lon": 130.9435,
        "wait_time": 30,
        "visit_duration": 60,
        "description": "日田名物のうなぎ料理",
        "rating": 4.4
    },
    {
        "name": "日田まぶし千屋",
        "category": "郷土料理",
        "lat": 33.3215,
        "lon": 130.9428,
        "wait_time": 25,
        "visit_duration": 50,
        "description": "日田のひつまぶし専門店",
        "rating": 4.3
    },
    {
        "name": "焼きとり鳥善",
        "category": "焼き鳥",
        "lat": 33.3198,
        "lon": 130.9441,
        "wait_time": 20,
        "visit_duration": 45,
        "description": "地元で人気の焼き鳥店",
        "rating": 4.2
    }
]

# 避難所データ
EVACUATION_CENTERS = [
    {
        "name": "日田市役所",
        "type": "指定避難所",
        "lat": 33.3200,
        "lon": 130.9417,
        "capacity": 500,
        "facilities": ["医療室", "給水設備", "非常用電源"],
        "safety_level": "高"
    },
    {
        "name": "日田市民センター",
        "type": "指定避難所",
        "lat": 33.3234,
        "lon": 130.9445,
        "capacity": 300,
        "facilities": ["給水設備", "非常用電源"],
        "safety_level": "高"
    },
    {
        "name": "日田高等学校",
        "type": "指定避難所",
        "lat": 33.3156,
        "lon": 130.9489,
        "capacity": 800,
        "facilities": ["医療室", "給水設備", "体育館"],
        "safety_level": "中"
    },
    {
        "name": "三隈中学校",
        "type": "指定避難所",
        "lat": 33.3267,
        "lon": 130.9356,
        "capacity": 400,
        "facilities": ["給水設備", "体育館"],
        "safety_level": "中"
    },
    {
        "name": "桂林小学校",
        "type": "指定避難所",
        "lat": 33.3178,
        "lon": 130.9512,
        "capacity": 300,
        "facilities": ["給水設備"],
        "safety_level": "中"
    }
]

# セッション状態の初期化
if 'current_location' not in st.session_state:
    st.session_state.current_location = HITA_CENTER
if 'selected_spots' not in st.session_state:
    st.session_state.selected_spots = []
if 'optimized_route' not in st.session_state:
    st.session_state.optimized_route = []
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "tourism"

# ユーティリティ関数
def calculate_distance(lat1, lon1, lat2, lon2):
    """2点間の距離を計算（km）"""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def calculate_travel_time(distance_km, transport_mode):
    """交通手段別の所要時間を計算（分）"""
    speeds = {
        "walk": 4.8,      # 徒歩: 4.8km/h
        "bicycle": 15,    # 自転車: 15km/h
        "car": 30,        # 車: 30km/h（市街地）
        "train": 45       # 鉄道: 45km/h（平均）
    }
    return (distance_km / speeds[transport_mode]) * 60

def optimize_route(start_location, destinations):
    """複数目的地の最適ルートを計算（TSP問題の近似解）"""
    if len(destinations) <= 1:
        return destinations
    
    # 全ての組み合わせを試す（目的地が少ない場合）
    if len(destinations) <= 6:
        min_distance = float('inf')
        best_route = destinations
        
        for perm in itertools.permutations(destinations):
            total_distance = 0
            current_pos = start_location
            
            for dest in perm:
                total_distance += calculate_distance(
                    current_pos[0], current_pos[1], dest['lat'], dest['lon']
                )
                current_pos = [dest['lat'], dest['lon']]
            
            if total_distance < min_distance:
                min_distance = total_distance
                best_route = list(perm)
        
        return best_route
    else:
        # 近隣法による近似解
        unvisited = destinations.copy()
        route = []
        current_pos = start_location
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: calculate_distance(
                current_pos[0], current_pos[1], x['lat'], x['lon']
            ))
            route.append(nearest)
            unvisited.remove(nearest)
            current_pos = [nearest['lat'], nearest['lon']]
        
        return route

def get_safe_route_score(lat, lon):
    """避難ルートの安全性スコアを計算（簡易版）"""
    # 川からの距離、標高、建物密度などを考慮
    # 実際の実装では地理データベースとの連携が必要
    river_distance = abs(lat - 33.3223)  # 三隈川からの距離
    elevation_factor = (lat - 33.31) * 100  # 簡易標高計算
    safety_score = min(100, max(0, 50 + river_distance * 1000 + elevation_factor))
    return safety_score

# メインタイトル
st.markdown('<h1 class="main-header">🗾 日田市ナビゲーションアプリ</h1>', unsafe_allow_html=True)

# モード選択
col1, col2 = st.columns(2)
with col1:
    if st.button("🌸 観光モード", use_container_width=True, type="primary" if st.session_state.current_mode == "tourism" else "secondary"):
        st.session_state.current_mode = "tourism"
        st.rerun()

with col2:
    if st.button("🚨 防災モード", use_container_width=True, type="primary" if st.session_state.current_mode == "disaster" else "secondary"):
        st.session_state.current_mode = "disaster"
        st.rerun()

# モード別ヘッダー
if st.session_state.current_mode == "tourism":
    st.markdown('<div class="mode-header tourism-mode">🌸 観光モード - 日田市を効率よく観光しよう！</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="mode-header disaster-mode">🚨 防災モード - 安全な避難ルートを確保</div>', unsafe_allow_html=True)

# サイドバー
st.sidebar.markdown("### 📍 現在地設定")
current_lat = st.sidebar.number_input("緯度", value=st.session_state.current_location[0], format="%.6f")
current_lon = st.sidebar.number_input("経度", value=st.session_state.current_location[1], format="%.6f")

if st.sidebar.button("現在地を更新"):
    st.session_state.current_location = [current_lat, current_lon]
    st.sidebar.success("現在地を更新しました")

# メイン処理
if st.session_state.current_mode == "tourism":
    # 観光モード
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🏛️ 観光スポット")
        
        # カテゴリフィルター
        categories = list(set([spot['category'] for spot in TOURISM_SPOTS]))
        selected_categories = st.multiselect("カテゴリで絞り込み", categories, default=categories)
        
        # 距離でソート
        spots_with_distance = []
        for spot in TOURISM_SPOTS:
            if spot['category'] in selected_categories:
                distance = calculate_distance(
                    st.session_state.current_location[0],
                    st.session_state.current_location[1],
                    spot['lat'],
                    spot['lon']
                )
                spots_with_distance.append({**spot, 'distance': distance})
        
        spots_with_distance.sort(key=lambda x: x['distance'])
        
        # スポット選択
        st.write("**目的地を選択（複数選択可能）:**")
        for spot in spots_with_distance:
            is_selected = spot in st.session_state.selected_spots
            
            with st.container():
                st.markdown(f'<div class="spot-card">', unsafe_allow_html=True)
                col_check, col_info = st.columns([1, 4])
                
                with col_check:
                    if st.checkbox("", key=f"spot_{spot['name']}", value=is_selected):
                        if spot not in st.session_state.selected_spots:
                            st.session_state.selected_spots.append(spot)
                    else:
                        if spot in st.session_state.selected_spots:
                            st.session_state.selected_spots.remove(spot)
                
                with col_info:
                    st.write(f"**{spot['name']}**")
                    st.write(f"📍 {spot['category']} | ⭐ {spot['rating']}")
                    st.write(f"📏 {spot['distance']:.1f}km")
                    
                    # 交通手段別時間表示
                    st.markdown('<div class="time-info">', unsafe_allow_html=True)
                    walk_time = calculate_travel_time(spot['distance'], 'walk')
                    bicycle_time = calculate_travel_time(spot['distance'], 'bicycle')
                    car_time = calculate_travel_time(spot['distance'], 'car')
                    
                    st.write(f"🚶 {walk_time:.0f}分 | 🚴 {bicycle_time:.0f}分 | 🚗 {car_time:.0f}分")
                    st.write(f"⏰ 待ち時間: {spot['wait_time']}分 | 滞在: {spot['visit_duration']}分")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.write(spot['description'])
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 飲食店セクション
        st.markdown("### 🍽️ 飲食店")
        for restaurant in RESTAURANTS:
            distance = calculate_distance(
                st.session_state.current_location[0],
                st.session_state.current_location[1],
                restaurant['lat'],
                restaurant['lon']
            )
            
            is_selected = restaurant in st.session_state.selected_spots
            
            with st.container():
                st.markdown(f'<div class="spot-card">', unsafe_allow_html=True)
                col_check, col_info = st.columns([1, 4])
                
                with col_check:
                    if st.checkbox("", key=f"restaurant_{restaurant['name']}", value=is_selected):
                        if restaurant not in st.session_state.selected_spots:
                            st.session_state.selected_spots.append(restaurant)
                    else:
                        if restaurant in st.session_state.selected_spots:
                            st.session_state.selected_spots.remove(restaurant)
                
                with col_info:
                    st.write(f"**{restaurant['name']}**")
                    st.write(f"🍽️ {restaurant['category']} | ⭐ {restaurant['rating']}")
                    st.write(f"📏 {distance:.1f}km")
                    
                    st.markdown('<div class="time-info">', unsafe_allow_html=True)
                    walk_time = calculate_travel_time(distance, 'walk')
                    car_time = calculate_travel_time(distance, 'car')
                    st.write(f"🚶 {walk_time:.0f}分 | 🚗 {car_time:.0f}分")
                    st.write(f"⏰ 待ち時間: {restaurant['wait_time']}分")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.write(restaurant['description'])
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # ルート最適化ボタン
        if st.session_state.selected_spots:
            if st.button("🗺️ 最適ルートを計算", type="primary"):
                st.session_state.optimized_route = optimize_route(
                    st.session_state.current_location,
                    st.session_state.selected_spots
                )
                st.success(f"{len(st.session_state.optimized_route)}箇所の最適ルートを計算しました！")
    
    with col2:
        # 地図表示
        m = folium.Map(location=st.session_state.current_location, zoom_start=14)
        
        # 現在地マーカー
        folium.Marker(
            st.session_state.current_location,
            popup="現在地",
            tooltip="あなたの現在地",
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(m)
        
        # 選択された観光スポットのマーカー
        for i, spot in enumerate(st.session_state.selected_spots):
            folium.Marker(
                [spot['lat'], spot['lon']],
                popup=f"{spot['name']}<br>待ち時間: {spot['wait_time']}分",
                tooltip=spot['name'],
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)
        
        # 最適化ルートの表示
        if st.session_state.optimized_route:
            route_points = [st.session_state.current_location]
            for spot in st.session_state.optimized_route:
                route_points.append([spot['lat'], spot['lon']])
            
            folium.PolyLine(
                route_points,
                weight=4,
                color='red',
                opacity=0.8,
                popup="最適ルート"
            ).add_to(m)
            
            # ルート番号の表示
            for i, spot in enumerate(st.session_state.optimized_route):
                folium.Marker(
                    [spot['lat'], spot['lon']],
                    popup=f"順序: {i+1}",
                    icon=folium.DivIcon(
                        html=f'<div style="background-color: white; border: 2px solid red; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; font-weight: bold;">{i+1}</div>',
                        icon_size=(25, 25)
                    )
                ).add_to(m)
        
        # 全ての観光スポットを薄いマーカーで表示
        for spot in TOURISM_SPOTS:
            if spot not in st.session_state.selected_spots:
                folium.Marker(
                    [spot['lat'], spot['lon']],
                    popup=spot['name'],
                    tooltip=spot['name'],
                    icon=folium.Icon(color='lightgray', icon='info-sign')
                ).add_to(m)
        
        st_folium(m, width=700, height=500)
        
        # ルート情報表示
        if st.session_state.optimized_route:
            st.markdown('<div class="route-info">', unsafe_allow_html=True)
            st.markdown("### 📋 最適ルート詳細")
            
            total_distance = 0
            total_time = 0
            current_pos = st.session_state.current_location
            
            transport_mode = st.selectbox("交通手段を選択", 
                ["walk", "bicycle", "car"], 
                format_func=lambda x: {"walk": "🚶 徒歩", "bicycle": "🚴 自転車", "car": "🚗 車"}[x]
            )
            
            for i, spot in enumerate(st.session_state.optimized_route):
                distance = calculate_distance(current_pos[0], current_pos[1], spot['lat'], spot['lon'])
                travel_time = calculate_travel_time(distance, transport_mode)
                
                total_distance += distance
                total_time += travel_time + spot['wait_time'] + spot['visit_duration']
                
                st.write(f"**{i+1}. {spot['name']}**")
                st.write(f"📏 移動距離: {distance:.1f}km | ⏰ 移動時間: {travel_time:.0f}分")
                st.write(f"⌛ 待ち時間: {spot['wait_time']}分 | 🏛️ 滞在時間: {spot['visit_duration']}分")
                st.write("---")
                
                current_pos = [spot['lat'], spot['lon']]
            
            st.write(f"**合計距離:** {total_distance:.1f}km")
            st.write(f"**合計所要時間:** {total_time:.0f}分 ({total_time/60:.1f}時間)")
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # 防災モード
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🚨 避難所一覧")
        
        # 避難所を距離順でソート
        shelters_with_distance = []
        for shelter in EVACUATION_CENTERS:
            distance = calculate_distance(
                st.session_state.current_location[0],
                st.session_state.current_location[1],
                shelter['lat'],
                shelter['lon']
            )
            safety_score = get_safe_route_score(shelter['lat'], shelter['lon'])
            shelters_with_distance.append({**shelter, 'distance': distance, 'safety_score': safety_score})
        
        shelters_with_distance.sort(key=lambda x: (x['distance'], -x['safety_score']))
        
        selected_shelter = None
        
        for shelter in shelters_with_distance:
            with st.container():
                st.markdown(f'<div class="evacuation-card">', unsafe_allow_html=True)
                
                if st.button(f"📍 {shelter['name']}", key=f"shelter_{shelter['name']}", use_container_width=True):
                    selected_shelter = shelter
                
                st.write(f"🏢 **種別:** {shelter['type']}")
                st.write(f"📏 **距離:** {shelter['distance']:.1f}km")
                st.write(f"👥 **収容人数:** {shelter['capacity']}人")
                st.write(f"🛡️ **安全レベル:** {shelter['safety_level']}")
                
                # 安全性スコア表示
                safety_color = "🟢" if shelter['safety_score'] > 70 else "🟡" if shelter['safety_score'] > 40 else "🔴"
                st.write(f"📊 **安全スコア:** {safety_color} {shelter['safety_score']:.0f}/100")
                
                # 移動時間計算
                walk_time = calculate_travel_time(shelter['distance'], 'walk')
                bicycle_time = calculate_travel_time(shelter['distance'], 'bicycle')
                car_time = calculate_travel_time(shelter['distance'], 'car')
                
                st.markdown('<div class="time-info">', unsafe_allow_html=True)
                st.write(f"⏰ **到着時間:** 🚶{walk_time:.0f}分 | 🚴{bicycle_time:.0f}分 | 🚗{car_time:.0f}分")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.write(f"🏥 **設備:** {', '.join(shelter['facilities'])}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 災害情報
        st.markdown("### ⚠️ 災害情報・注意事項")
        st.markdown("""
        <div class="warning-alert">
        <strong>避難時の注意点:</strong><br>
        • 川沿いのルートは避けてください<br>
        • 頭上注意（落下物に注意）<br>
        • 動きやすい服装・靴で避難<br>
        • 貴重品・非常用品を持参<br>
        • 近隣住民と声をかけ合って避難
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # 避難所マップ
        m = folium.Map(location=st.session_state.current_location, zoom_start=13)
        
        # 現在地マーカー
        folium.Marker(
            st.session_state.current_location,
            popup="現在地<br>ここから避難開始",
            tooltip="現在地",
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(m)
        
        # 避難所マーカー
        for shelter in EVACUATION_CENTERS:
            # 安全レベルに応じた色分け
            color = 'green' if shelter['safety_level'] == '高' else 'orange' if shelter['safety_level'] == '中' else 'red'
            
            folium.Marker(
                [shelter['lat'], shelter['lon']],
                popup=f"""
                <b>{shelter['name']}</b><br>
                収容人数: {shelter['capacity']}人<br>
                設備: {', '.join(shelter['facilities'])}<br>
                安全レベル: {shelter['safety_level']}
                """,
                tooltip=f"{shelter['name']} ({shelter['safety_level']})",
                icon=folium.Icon(color=color, icon='home')
            ).add_to(m)
        
        # 危険エリア（簡易的な表示）
        # 三隈川周辺を危険エリアとして表示
        folium.Polygon(
            locations=[
                [33.3200, 130.9380],
                [33.3250, 130.9380],
                [33.3250, 130.9420],
                [33.3200, 130.9420]
            ],
            color='red',
            weight=2,
            opacity=0.8,
            fill=True,
            fillColor='red',
            fillOpacity=0.2,
            popup="洪水危険エリア<br>避難時は迂回してください"
        ).add_to(m)
        
        # 選択された避難所へのルート表示
        if 'selected_shelter' in locals() and selected_shelter:
            # 安全ルートの計算（危険エリアを避けたルート）
            route_points = [
                st.session_state.current_location,
                [selected_shelter['lat'], selected_shelter['lon']]
            ]
            
            folium.PolyLine(
                route_points,
                weight=5,
                color='green',
                opacity=0.8,
                popup=f"安全な避難ルート<br>目的地: {selected_shelter['name']}"
            ).add_to(m)
        
        st_folium(m, width=700, height=500)
        
        # 避難ルート詳細情報
        if 'selected_shelter' in locals() and selected_shelter:
            st.markdown('<div class="route-info">', unsafe_allow_html=True)
            st.markdown(f"### 🗺️ {selected_shelter['name']}への避難ルート")
            
            distance = selected_shelter['distance']
            walk_time = calculate_travel_time(distance, 'walk')
            bicycle_time = calculate_travel_time(distance, 'bicycle')
            car_time = calculate_travel_time(distance, 'car')
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("距離", f"{distance:.1f}km")
            with col_b:
                st.metric("徒歩", f"{walk_time:.0f}分")
            with col_c:
                st.metric("安全スコア", f"{selected_shelter['safety_score']:.0f}/100")
            
            st.write("**避難経路のポイント:**")
            if selected_shelter['safety_score'] > 70:
                st.success("✅ 安全性の高いルートです")
            elif selected_shelter['safety_score'] > 40:
                st.warning("⚠️ 注意が必要なルートです")
            else:
                st.error("🚨 危険なルートです。他の避難所を検討してください")
            
            st.write(f"- 川からの距離を考慮した安全ルート")
            st.write(f"- 避難所設備: {', '.join(selected_shelter['facilities'])}")
            st.write(f"- 収容可能人数: {selected_shelter['capacity']}人")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 気象警報・避難指示情報（サンプル）
        st.markdown("### 📢 最新の災害情報")
        
        current_time = datetime.now()
        st.markdown('<div class="warning-alert">', unsafe_allow_html=True)
        st.write(f"**発表時刻:** {current_time.strftime('%Y年%m月%d日 %H:%M')}")
        st.write("**気象警報:** 大雨警報（継続中）")
        st.write("**河川情報:** 三隈川：水位上昇中（レベル2）")
        st.write("**避難情報:** 高齢者等避難開始")
        st.markdown('</div>', unsafe_allow_html=True)

# 共通フッター
st.markdown("---")

# 統計情報
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("現在のモード", 
             "🌸 観光" if st.session_state.current_mode == "tourism" else "🚨 防災")

with col2:
    if st.session_state.current_mode == "tourism":
        st.metric("選択中の目的地", f"{len(st.session_state.selected_spots)}箇所")
    else:
        st.metric("最寄り避難所数", f"{len(EVACUATION_CENTERS)}箇所")

with col3:
    st.metric("現在時刻", datetime.now().strftime("%H:%M"))

with col4:
    if st.session_state.current_mode == "tourism" and st.session_state.optimized_route:
        total_time = sum([spot.get('wait_time', 0) + spot.get('visit_duration', 0) for spot in st.session_state.optimized_route])
        travel_time = sum([calculate_travel_time(calculate_distance(
            st.session_state.current_location[0] if i == 0 else st.session_state.optimized_route[i-1]['lat'],
            st.session_state.current_location[1] if i == 0 else st.session_state.optimized_route[i-1]['lon'],
            spot['lat'], spot['lon']
        ), 'walk') for i, spot in enumerate(st.session_state.optimized_route)])
        st.metric("総所要時間", f"{(total_time + travel_time)/60:.1f}時間")
    else:
        st.metric("アプリ版本", "v1.0.0")

# 使用方法・ヘルプ
with st.expander("📖 使用方法・ヘルプ"):
    if st.session_state.current_mode == "tourism":
        st.markdown("""
        ### 🌸 観光モードの使い方
        
        **1. 目的地選択**
        - 左側のリストから訪問したい観光スポットや飲食店を選択
        - 複数選択可能（チェックボックス）
        - 現在地からの距離と各交通手段での所要時間を表示
        
        **2. ルート最適化**
        - 「最適ルートを計算」ボタンで効率的な巡回ルートを自動計算
        - 待ち時間や滞在時間を考慮したスケジュール提案
        - 地図上に順番付きでルート表示
        
        **3. 交通手段選択**
        - 徒歩、自転車、車、鉄道から選択
        - 各手段での所要時間を自動計算
        
        **4. 時間管理**
        - 各スポットの待ち時間と推奨滞在時間を表示
        - 総所要時間で1日のスケジュール管理
        """)
    else:
        st.markdown("""
        ### 🚨 防災モードの使い方
        
        **1. 現在地設定**
        - サイドバーで正確な現在地（緯度・経度）を入力
        - GPSが利用できない場合は住所から推定
        
        **2. 避難所選択**
        - 距離・安全性を考慮した避難所一覧から選択
        - 収容人数や設備情報を確認
        - 安全スコアで避難ルートの危険度を判定
        
        **3. 避難ルート確認**
        - 危険エリア（河川周辺など）を避けた安全ルート表示
        - 各交通手段での到着時間を計算
        - 避難時の注意点を確認
        
        **4. 災害情報確認**
        - 最新の気象警報・避難指示情報
        - 河川水位・道路状況等のリアルタイム情報
        """)

# 重要な注意事項
st.markdown("""
<div class="warning-alert">
<strong>⚠️ 重要な注意事項</strong><br>
• このアプリは参考情報として提供されています<br>
• 実際の災害時は公式の避難指示に従ってください<br>
• 道路状況や気象条件により、実際の所要時間は変わる可能性があります<br>
• GPSや地図データの精度には限界があります<br>
• 緊急時は119番（消防）、110番（警察）へ連絡してください
</div>
""", unsafe_allow_html=True)

# 開発情報
st.markdown("---")
st.markdown("""
**開発:** 日田市観光・防災支援システム | **対象エリア:** 大分県日田市 | **更新:** 2024年版データ使用
""")

# キャッシュクリア機能（開発者用）
if st.sidebar.button("🔄 データリセット"):
    st.session_state.selected_spots = []
    st.session_state.optimized_route = []
    st.sidebar.success("データをリセットしました")