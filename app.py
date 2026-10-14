import streamlit as st
import pandas as pd
import os
import json
from PIL import Image

st.set_page_config(page_title="表面科学技術者 一問一答", layout="centered", initial_sidebar_state="collapsed")

csv_path = "表面科学技術者資格認定問題集_統合版.csv"
progress_file = "progress.json"  # 🌟 セーブデータ用のファイル名

@st.cache_data
def load_data():
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path).fillna("")
        if "分野" not in df.columns:
            df["分野"] = "基礎編"
        df["ID"] = df["分野"] + "_" + df["問題番号"]
        return df
    return None

df = load_data()

if df is None or df.empty:
    st.error(f"データファイル「{csv_path}」が見つかりません。")
    st.stop()

# 🌟 セーブデータを読み込む関数
def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"bookmarks": [], "solved": []}

# 🌟 セーブデータを保存する関数
def save_progress():
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({
            "bookmarks": st.session_state.bookmarks,
            "solved": st.session_state.solved
        }, f, ensure_ascii=False, indent=4)

# --- セッション（状態）の初期化 ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'selected_field' not in st.session_state: st.session_state.selected_field = '基礎編'
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'show_answer' not in st.session_state: st.session_state.show_answer = False

# 🌟 起動時にセーブデータからチェック状況を読み込む
if 'bookmarks' not in st.session_state or 'solved' not in st.session_state:
    progress = load_progress()
    st.session_state.bookmarks = progress.get("bookmarks", [])
    st.session_state.solved = progress.get("solved", [])

def go_home(): st.session_state.page = 'home'
def go_list(field):
    st.session_state.selected_field = field
    st.session_state.page = 'list'
def go_question(idx):
    st.session_state.current_idx = idx
    st.session_state.show_answer = False
    st.session_state.page = 'question'

# ==========================================
# 1. ホーム画面
# ==========================================
if st.session_state.page == 'home':
    st.title("🏠 ホーム：分野選択")
    st.write("学習したい分野を選んでください。")
    
    fields = df["分野"].unique()
    for field in fields:
        if st.button(f"📘 {field}", width="stretch"):
            go_list(field)
            st.rerun()

# ==========================================
# 2. 問題一覧画面
# ==========================================
elif st.session_state.page == 'list':
    st.title(f"📂 {st.session_state.selected_field}")
    st.button("🏠 ホームへ戻る", on_click=go_home)
    
    field_df = df[df["分野"] == st.session_state.selected_field].reset_index()
    
    if field_df.empty:
        st.warning("この分野の問題はまだ登録されていません。")
    else:
        st.write("### 📝 問題一覧")
        st.caption("凡例: ⬜ 未解答 / ✅ 解答済 / 🚩 復習チェック")
        st.markdown("---")
        
        cols = st.columns(5)
        for i, row in field_df.iterrows():
            col = cols[i % 5]
            
            if row["ID"] in st.session_state.bookmarks:
                icon = "🚩"
            elif row["ID"] in st.session_state.solved:
                icon = "✅"
            else:
                icon = "⬜"
                
            label = f"{icon} {row['問題番号']}"
            
            if col.button(label, key=f"btn_{row['ID']}", width="stretch"):
                go_question(row['index'])
                st.rerun()

# ==========================================
# 3. 問題画面
# ==========================================
elif st.session_state.page == 'question':
    col_h, col_l = st.columns(2)
    with col_h: st.button("🏠 ホームへ", on_click=go_home, width="stretch")
    with col_l: st.button("📂 一覧へ戻る", on_click=lambda: go_list(st.session_state.selected_field), width="stretch")
        
    st.markdown("---")
    
    row = df.loc[st.session_state.current_idx]
    st.subheader(f"{row['分野']} - {row['問題番号']}")
    
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        is_solved_ui = st.checkbox("✅ 解答済みにする", value=(row['ID'] in st.session_state.solved))
        if is_solved_ui and row['ID'] not in st.session_state.solved:
            st.session_state.solved.append(row['ID'])
            save_progress() # 🌟 変更したら即セーブ
        elif not is_solved_ui and row['ID'] in st.session_state.solved:
            st.session_state.solved.remove(row['ID'])
            save_progress() # 🌟 変更したら即セーブ
            
    with col_chk2:
        is_bookmarked_ui = st.checkbox("🚩 復習リストに入れる", value=(row['ID'] in st.session_state.bookmarks))
        if is_bookmarked_ui and row['ID'] not in st.session_state.bookmarks:
            st.session_state.bookmarks.append(row['ID'])
            save_progress() # 🌟 変更したら即セーブ
        elif not is_bookmarked_ui and row['ID'] in st.session_state.bookmarks:
            st.session_state.bookmarks.remove(row['ID'])
            save_progress() # 🌟 変更したら即セーブ
    
    st.write("📝 **問題**")
    if row['問題画像'] and os.path.exists(row['問題画像']):
        st.image(Image.open(row['問題画像']), width="stretch")
    else:
        st.warning("問題画像がありません。")
        
    st.markdown("---")
    
    if not st.session_state.show_answer:
        if st.button("💡 解答・解説を確認", width="stretch"):
            st.session_state.show_answer = True
            if row['ID'] not in st.session_state.solved:
                st.session_state.solved.append(row['ID'])
                save_progress() # 🌟 変更したら即セーブ
            st.rerun()
    else:
        st.write("📖 **解答・解説**")
        if row['解説画像'] and os.path.exists(row['解説画像']):
            st.image(Image.open(row['解説画像']), width="stretch")
        elif not row['解説画像']:
            st.info("この問題には解説がありません。")
        else:
            st.error("解説画像ファイルが見つかりません。")
            
    st.markdown("---")
    
    field_indices = df[df["分野"] == st.session_state.selected_field].index.tolist()
    current_pos = field_indices.index(st.session_state.current_idx)
    
    col_prev, col_next = st.columns(2)
    with col_prev:
        if current_pos > 0:
            if st.button("⏪ 前へ", width="stretch"):
                go_question(field_indices[current_pos - 1])
                st.rerun()
    with col_next:
        if current_pos < len(field_indices) - 1:
            if st.button("次へ ⏭️", width="stretch"):
                go_question(field_indices[current_pos + 1])
                st.rerun()
        else:
            st.success("最後の問題です！🎉")