import os
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
from io import BytesIO

# 데이터베이스 파일 경로 설정
DB_DIR = os.path.join(os.path.expanduser('~'), '.student_assessment_data')
DB_FILE = os.path.join(DB_DIR, 'student_assessments.db')

# 디렉토리가 없으면 생성
os.makedirs(DB_DIR, exist_ok=True)

# 데이터베이스 연결
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# 테이블 생성
c.execute('''CREATE TABLE IF NOT EXISTS students
             (student_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              class INTEGER NOT NULL,
              number INTEGER NOT NULL,
              learning_style TEXT,
              mbti_type TEXT,
              interests TEXT,
              collaboration_skill INTEGER,
              digital_literacy INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS grades
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id TEXT NOT NULL,
              subject TEXT NOT NULL,
              score REAL NOT NULL,
              FOREIGN KEY (student_id) REFERENCES students(student_id))''')

conn.commit()

def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'intro'
    if 'student_data' not in st.session_state:
        st.session_state.student_data = {}
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'submit_clicked' not in st.session_state:
        st.session_state.submit_clicked = False

def generate_student_id(class_num, student_num):
    return f"1{class_num:02d}{student_num:02d}"

def intro_page():
    st.title("1학년 학생 사전 조사")
    st.write("이 조사는 여러분의 학습 스타일, 성격 유형, 관심사 등을 파악하여 모둠 편성에 활용하기 위한 것입니다.")
    st.write("모든 질문에 정직하게 답변해 주시기 바랍니다.")

    class_num = st.selectbox("학급을 선택해주세요", list(range(1, 8)))
    student_num = st.number_input("번호를 입력해주세요", min_value=1, max_value=26, step=1)
    name = st.text_input("이름을 입력해주세요")

    if st.button("시작하기"):
        if name and class_num and student_num:
            st.session_state.submit_clicked = True
            st.session_state.student_data['student_id'] = generate_student_id(class_num, student_num)
            st.session_state.student_data['name'] = name
            st.session_state.student_data['class'] = class_num
            st.session_state.student_data['number'] = student_num
        else:
            st.warning("모든 필드를 입력해주세요.")

    if st.session_state.submit_clicked:
        if st.button("제출하시겠습니까?"):
            c.execute("SELECT * FROM students WHERE student_id = ?", (st.session_state.student_data['student_id'],))
            existing_student = c.fetchone()

            if existing_student:
                st.warning("이미 조사를 완료한 학생입니다. 기존 데이터를 업데이트합니다.")
            else:
                c.execute("INSERT INTO students (student_id, name, class, number) VALUES (?, ?, ?, ?)",
                          (st.session_state.student_data['student_id'], st.session_state.student_data['name'],
                           st.session_state.student_data['class'], st.session_state.student_data['number']))
                conn.commit()
            
            st.session_state.page = 'learning_style'
            st.session_state.submit_clicked = False
            st.rerun()

def learning_style_assessment():
    st.title("학습 스타일 평가")
    st.write("다음 질문들에 답하여 여러분의 학습 스타일을 파악해봅시다.")

    q1 = st.radio("1. 새로운 정보를 배울 때, 나는 주로:", 
                  ["그림이나 도표를 보는 것이 도움이 된다", 
                   "설명을 듣는 것이 도움이 된다", 
                   "직접 해보는 것이 도움이 된다"])
    q2 = st.radio("2. 수업 시간에 나는 주로:", 
                  ["필기를 많이 한다", 
                   "선생님의 설명을 주의 깊게 듣는다", 
                   "움직이거나 무언가를 만지작거린다"])

    if st.button("다음"):
        st.session_state.submit_clicked = True
        if q1.startswith("그림") and q2.startswith("필기"):
            st.session_state.student_data['learning_style'] = "시각적"
        elif q1.startswith("설명") and q2.startswith("선생님"):
            st.session_state.student_data['learning_style'] = "청각적"
        else:
            st.session_state.student_data['learning_style'] = "운동감각적"

    if st.session_state.submit_clicked:
        if st.button("제출하시겠습니까?"):
            st.session_state.page = 'mbti'
            st.session_state.submit_clicked = False
            st.rerun()

def mbti_assessment():
    st.title("MBTI 성격 유형 검사")
    st.write("다음 질문들에 답하여 여러분의 MBTI 성격 유형을 파악해봅시다.")

    e_i = st.radio("1. 나는 주로:", ["사람들과 어울리는 것을 좋아한다 (E)", "혼자 있는 시간을 즐긴다 (I)"])
    s_n = st.radio("2. 나는 주로:", ["구체적인 사실에 집중한다 (S)", "가능성과 의미를 찾는다 (N)"])
    t_f = st.radio("3. 결정을 내릴 때 나는 주로:", ["논리와 사실에 기반한다 (T)", "감정과 가치에 기반한다 (F)"])
    j_p = st.radio("4. 나는 주로:", ["계획을 세우고 그대로 실행한다 (J)", "상황에 따라 유연하게 대처한다 (P)"])

    if st.button("다음"):
        st.session_state.submit_clicked = True
        st.session_state.student_data['mbti_type'] = (e_i[-2] + s_n[-2] + t_f[-2] + j_p[-2])

    if st.session_state.submit_clicked:
        if st.button("제출하시겠습니까?"):
            st.session_state.page = 'interests'
            st.session_state.submit_clicked = False
            st.rerun()

def interests_assessment():
    st.title("관심사 조사")
    st.write("여러분의 관심사에 대해 알려주세요.")

    if 'interests' not in st.session_state:
        st.session_state.interests = []

    interests = st.multiselect(
        "관심 있는 분야를 모두 선택해주세요",
        ["국어", "수학", "영어", "과학", "사회", "음악", "미술", "체육", "기술가정", "한국사"],
        default=st.session_state.interests
    )

    st.session_state.interests = interests

    if st.button("다음"):
        if interests:
            st.session_state.submit_clicked = True
            st.session_state.student_data['interests'] = ", ".join(interests)
        else:
            st.warning("최소 하나의 관심사를 선택해주세요.")

    if st.session_state.submit_clicked:
        if st.button("제출하시겠습니까?"):
            st.session_state.page = 'skills'
            st.session_state.submit_clicked = False
            st.rerun()

def skills_assessment():
    st.title("기술 평가")
    st.write("여러분의 협업 능력과 디지털 리터러시를 평가해봅시다.")

    collaboration = st.slider("1에서 5까지, 여러분의 협업 능력을 어떻게 평가하시나요?", 1, 5, 3)
    digital_literacy = st.slider("1에서 5까지, 여러분의 디지털 기기 활용 능력을 어떻게 평가하시나요?", 1, 5, 3)

    if st.button("완료"):
        st.session_state.submit_clicked = True
        st.session_state.student_data['collaboration_skill'] = collaboration
        st.session_state.student_data['digital_literacy'] = digital_literacy

    if st.session_state.submit_clicked:
        if st.button("제출하시겠습니까?"):
            st.session_state.page = 'result'
            st.session_state.submit_clicked = False
            st.rerun()

def save_assessment_data():
    data = st.session_state.student_data
    c.execute("""UPDATE students 
                 SET learning_style = ?, mbti_type = ?, interests = ?, 
                     collaboration_skill = ?, digital_literacy = ?
                 WHERE student_id = ?""",
              (data['learning_style'], data['mbti_type'], data['interests'],
               data['collaboration_skill'], data['digital_literacy'], data['student_id']))
    conn.commit()

def result_page():
    st.title("조사 결과")
    data = st.session_state.student_data
    st.write(f"학급: {data['class']}반")
    st.write(f"번호: {data['number']}번")
    st.write(f"이름: {data['name']}")
    st.write(f"학습 스타일: {data['learning_style']}")
    st.write(f"MBTI 성격 유형: {data['mbti_type']}")
    st.write(f"관심사: {data['interests']}")
    st.write(f"협업 능력: {data['collaboration_skill']}")
    st.write(f"디지털 리터러시: {data['digital_literacy']}")

    save_assessment_data()

    st.success("조사가 완료되었습니다. 결과가 저장되었습니다.")

    if st.button("처음으로"):
        st.session_state.page = 'intro'
        st.session_state.student_data = {}
        st.rerun()

def verify_password(password):
    # 실제 구현에서는 보다 안전한 방법으로 비밀번호를 저장하고 검증해야 합니다
    return hashlib.sha256(password.encode()).hexdigest() == "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

def admin_login():
    st.title("관리자 로그인")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if verify_password(password):
            st.session_state.admin_authenticated = True
            st.success("로그인 성공!")
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

def admin_page():
    if not st.session_state.get('admin_authenticated', False):
        admin_login()
    else:
        st.title("관리자 페이지")

        st.subheader("성적 입력")
        input_method = st.radio("입력 방식 선택", ["개별 입력", "CSV 파일 업로드"])

        if input_method == "개별 입력":
            individual_grade_input()
        else:
            csv_grade_upload()

        display_student_data()

        if st.button("로그아웃"):
            st.session_state.admin_authenticated = False
            st.rerun()

def individual_grade_input():
    student_id = st.text_input("학생 ID (예: 10315)")
    subject = st.selectbox("과목", ["국어", "수학", "영어", "과학", "사회", "음악", "미술", "체육", "기술가정", "한국사"])
    score = st.number_input("점수", min_value=0, max_value=100, step=1)

    if st.button("성적 입력"):
        if st.button("제출하시겠습니까?"):
            if student_id and subject and score:
                c.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
                if c.fetchone():
                    c.execute("INSERT INTO grades (student_id, subject, score) VALUES (?, ?, ?)",
                              (student_id, subject, score))
                    conn.commit()
                    st.success(f"{student_id} 학생의 {subject} 성적 {score}점이 입력되었습니다.")
                else:
                    st.error("존재하지 않는 학생 ID입니다.")
            else:
                st.error("모든 필드를 입력해주세요.")

def csv_grade_upload():
    st.write("CSV 파일 형식:")
    st.write("1열: 학번 (student_id)")
    st.write("2열: 과목 (subject)")
    st.write("3열: 점수 (score)")
    st.write("첫 번째 행은 헤더로 처리되므로, 실제 데이터는 2행부터 입력하세요.")

    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")
    if uploaded_file is not None:
        if st.button("업로드하시겠습니까?"):
            try:
                df = pd.read_csv(uploaded_file, header=0, names=['student_id', 'subject', 'score'])

                success_count = 0
                error_count = 0
                for _, row in df.iterrows():
                    c.execute("SELECT * FROM students WHERE student_id = ?", (row['student_id'],))
                    if c.fetchone():
                        c.execute("INSERT INTO grades (student_id, subject, score) VALUES (?, ?, ?)",
                                  (row['student_id'], row['subject'], row['score']))
                        success_count += 1
                    else:
                        error_count += 1

                conn.commit()
                st.success(f"{success_count}개의 성적이 성공적으로 입력되었습니다.")
                if error_count > 0:
                    st.warning(f"{error_count}개의 성적은 존재하지 않는 학생 ID로 인해 입력되지 않았습니다.")
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

def display_student_data():
    st.subheader("전체 학생 데이터")
    try:
        c.execute("""SELECT s.student_id, s.name, s.class, s.number, s.learning_style, s.mbti_type, 
                            s.interests, s.collaboration_skill, s.digital_literacy,
                            GROUP_CONCAT(g.subject || ':' || g.score, ', ') as grades
                     FROM students s
                     LEFT JOIN grades g ON s.student_id = g.student_id
                     GROUP BY s.student_id""")
        data = c.fetchall()
        if data:
            df = pd.DataFrame(data, columns=['학생ID', '이름', '학급', '번호', '학습스타일', 'MBTI', '관심사', 
                                             '협업능력', '디지털리터러시', '성적'])
            st.dataframe(df)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='학생데이터')

            st.download_button(
                label="Excel 파일 다운로드",
                data=output.getvalue(),
                file_name="student_data_with_grades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("등록된 학생 데이터가 없습니다.")
    except sqlite3.Error as e:
        st.error(f"데이터베이스 오류: {e}")
        st.info("데이터베이스에 테이블이 없거나 데이터가 비어있을 수 있습니다.")

def main():
    init_session_state()

    page = st.sidebar.radio("페이지 선택", ["학생 조사", "관리자 페이지"])

    if page == "학생 조사":
        if st.session_state.page == 'intro':
            intro_page()
        elif st.session_state.page == 'learning_style':
            learning_style_assessment()
        elif st.session_state.page == 'mbti':
            mbti_assessment()
        elif st.session_state.page == 'interests':
            interests_assessment()
        elif st.session_state.page == 'skills':
            skills_assessment()
        elif st.session_state.page == 'result':
            result_page()
    else:
        admin_page()

if __name__ == "__main__":
    main()
