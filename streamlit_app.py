import streamlit as st
import pandas as pd
import numpy as np
import random
import math
import re
import io
import time
from itertools import combinations, permutations

# Custom CSS for iOS-style UI
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .student-list-box {
        background: rgba(255, 249, 196, 0.85);
        border: 1px solid rgba(245, 127, 23, 0.15);
        border-radius: 16px;
        padding: 18px;
        margin: 16px 0;
        column-count: 5;
        column-gap: 24px;
    }
    .student-list-box p {
        margin: 0 0 16px 0;
        font-weight: 700;
        color: #5d4037;
    }
    .student-list-box .student-name {
        margin-bottom: 8px;
        line-height: 1.6;
    }
    .step-header {
        background: linear-gradient(135deg, #22714b, #2d8a5f);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
        font-weight: 600;
    }
    .btn-primary {
        background-color: #22714b !important;
        border-color: #22714b !important;
        border-radius: 8px;
        font-weight: 500;
    }
    .st-key-finalize button {
        background-color: #fff9c4 !important;
        border-color: #ffecb3 !important;
        color: #000 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .st-key-finalize button:hover {
        background-color: #fff59d !important;
    }
    .btn-secondary {
        background-color: #6c757d !important;
        border-color: #6c757d !important;
        border-radius: 8px;
    }
    .stTextInput, .stNumberInput, .stTextArea {
        border-radius: 8px;
        border: 1px solid #ced4da;
    }
    .seat-card {
        background: #e3f2fd;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        text-align: center;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        font-size: 18px;
    }
    .group-header {
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 15px;
        color: #22714b;
    }
    .stNumberInput input {
        text-align: center !important;
    }
    .stNumberInput label {
        text-align: center !important;
        display: block !important;
    }
    .stAlert {
        text-align: center !important;
    }
    .front-seat { background-color: #e3f2fd; }
    .back-seat { background-color: #e3f2fd; }
    .warning { color: #dc3545; font-weight: 500; }
    .success { color: #22714b; font-weight: 500; }
    .progress-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 8px;
        margin: 10px 0;
    }
    .progress-fill {
        background: #22714b;
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화 (맨 먼저 실행)
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'students' not in st.session_state:
    st.session_state.students = []
if 'seats' not in st.session_state:
    st.session_state.seats = []
if 'balance_students' not in st.session_state:
    st.session_state.balance_students = []
if 'separation_groups' not in st.session_state:
    st.session_state.separation_groups = []
if 'front_priority' not in st.session_state:
    st.session_state.front_priority = []
if 'back_priority' not in st.session_state:
    st.session_state.back_priority = []
if 'arrangement' not in st.session_state:
    st.session_state.arrangement = {}
if 'seat_layout' not in st.session_state:
    st.session_state.seat_layout = {}
if 'arrangement_version' not in st.session_state:
    st.session_state.arrangement_version = 0
if 'student_random_ready' not in st.session_state:
    st.session_state.student_random_ready = False

# 앱 제목
st.title("🎓 똑똑한 자리 배치 도우미")
st.markdown("초등학교 학급 자리 바꾸기를 쉽고 스마트하게!")
st.divider()

if st.session_state.step == 0:
    st.markdown("""<div style='text-align: center; padding: 30px 20px;'>
<h2 style='color: #22714b; margin: 0;'>👋 환영합니다!</h2>
<p style='font-size: 16px; color: #333; margin: 15px 0;'>우리 반 자리 바꾸기를 시작해 볼까요?<br>단계별로 안내해 드릴게요.</p>
</div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("🚀 시작하기", key="start", help="자리 배치 과정을 시작합니다", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

# 유틸리티 함수들
def parse_student_input(text):
    """학생 명단 텍스트 파싱"""
    lines = text.strip().split('\n')
    students = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 번호, 이름 형식 파싱
        match = re.match(r'^(\d+)\s*[,\-\s]\s*(.+)$', line)
        if match:
            num, name = match.groups()
            students.append({'번호': int(num), '이름': name.strip()})
        else:
            # 이름만 있는 경우
            students.append({'번호': len(students)+1, '이름': line.strip()})
    return pd.DataFrame(students)

def load_csv_file(uploaded_file):
    """CSV 파일 로드 및 파싱"""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        # 컬럼명 유추
        col_map = {}
        for col in df.columns:
            if '번호' in col or 'num' in col.lower():
                col_map['번호'] = col
            elif '이름' in col or 'name' in col.lower() or '학생' in col:
                col_map['이름'] = col
        
        if '번호' not in col_map:
            df['번호'] = range(1, len(df)+1)
        else:
            df = df.rename(columns={col_map['번호']: '번호'})
        
        if '이름' not in col_map:
            st.error("이름 컬럼을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        df = df.rename(columns={col_map['이름']: '이름'})
        df = df[['번호', '이름']].dropna()
        return df
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류: {str(e)}")
        return pd.DataFrame()


def create_student_template_csv():
    """학생 명단 업로드를 위한 CSV 예시 파일 생성"""
    template_df = pd.DataFrame({
        '번호': [1, 2, 3, 4],
        '이름': ['김민준', '박서연', '김원필', '윤도운']
    })
    csv_bytes = template_df.to_csv(index=False, encoding='cp949').encode('cp949', errors='replace')
    return csv_bytes


def sort_seat_key(seat):
    return (seat['분단'], seat['행'], seat['열'])


def assign_priority_students(seats, front_priority, back_priority):
    """앞줄/뒷줄 우선 학생을 가능한 한 전방/후방에 고정 배치"""
    seat_by_id = {seat['좌석번호']: seat for seat in seats}
    available = set(seat_by_id.keys())
    arrangement = {}

    front_priority = [s for s in front_priority if s]
    back_priority = [s for s in back_priority if s]
    random.shuffle(front_priority)
    random.shuffle(back_priority)

    front_seats = [seat for seat in seats if seat['앞줄']]
    non_back_seats = [seat for seat in seats if not seat['뒷줄'] and seat not in front_seats]
    selected_front = []
    if len(front_priority) <= len(front_seats):
        selected_front = random.sample(front_seats, len(front_priority))
    else:
        selected_front = front_seats.copy()
        needed = len(front_priority) - len(front_seats)
        selected_front += random.sample(non_back_seats, min(needed, len(non_back_seats)))

    for student, seat in zip(front_priority, selected_front):
        arrangement[student] = seat['좌석번호']
        available.remove(seat['좌석번호'])

    back_seats = [seat for seat in seats if seat['뒷줄']]
    non_front_seats = [seat for seat in seats if not seat['앞줄'] and seat not in back_seats]
    selected_back = []
    if len(back_priority) <= len(back_seats):
        selected_back = random.sample(back_seats, len(back_priority))
    else:
        selected_back = back_seats.copy()
        needed = len(back_priority) - len(back_seats)
        selected_back += random.sample(non_front_seats, min(needed, len(non_front_seats)))

    for student, seat in zip(back_priority, selected_back):
        if seat['좌석번호'] in available:
            arrangement[student] = seat['좌석번호']
            available.remove(seat['좌석번호'])

    return arrangement, available


def build_seat_layout(num_groups, seats_per_group):
    """좌석 구조 생성"""
    seats = []
    group_x = {i: i*10 for i in range(num_groups)}  # 분단 간 거리
    
    for group in range(num_groups):
        rows = seats_per_group[group]  # 한 분단당 한 열로 세로 배치
        for row in range(rows):
            if rows <= 3:
                back_seat = row == rows - 1
            else:
                back_seat = 3 <= row <= 4
            seat = {
                '분단': group + 1,
                '행': row,
                '열': 0,
                'x': group_x[group],
                'y': row,
                '앞줄': row < 2,
                '뒷줄': back_seat,
                '좌석번호': len(seats) + 1
            }
            seats.append(seat)
    return seats

def calculate_distance(seat1, seat2):
    """좌석 간 거리 계산"""
    return math.sqrt((seat1['x'] - seat2['x'])**2 + (seat1['y'] - seat2['y'])**2)


def is_preferred_front_seat(seat):
    return seat['앞줄']


def is_preferred_back_seat(seat):
    return seat['뒷줄']


def score_arrangement(arrangement, seats, balance_students, separation_groups, front_priority, back_priority):
    """배치 점수 계산"""
    score = 0
    
    # 모둠 균형 배치 점수
    balance_groups = set()
    for student in balance_students:
        if student in arrangement:
            seat = next(s for s in seats if s['좌석번호'] == arrangement[student])
            balance_groups.add(seat['분단'])
    if len(balance_students) <= len({s['분단'] for s in seats}) and len(balance_groups) != len(balance_students):
        return -1000000
    score += len(balance_groups) * 10  # 서로 다른 분단에 배치될수록 점수 +
    
    # 분리 배치 점수
    for group in separation_groups:
        group_seats = [next(s for s in seats if s['좌석번호'] == arrangement[student]) for student in group if student in arrangement]
        if len(group_seats) > 1:
            groups = [seat['분단'] for seat in group_seats]
            if len(groups) != len(set(groups)):
                return -1000000  # 같은 분단에 있으면 허용하지 않음
            distances = [calculate_distance(s1, s2) for s1, s2 in combinations(group_seats, 2)]
            score += sum(distances) * 6  # 거리 합 최대화
    
    # 앞줄 우선 필수 조건
    for student in front_priority:
        if student in arrangement:
            seat = next(s for s in seats if s['좌석번호'] == arrangement[student])
            if not is_preferred_front_seat(seat):
                return -1000000
            score += 10
    
    # 뒷줄 우선 필수 조건
    for student in back_priority:
        if student in arrangement:
            seat = next(s for s in seats if s['좌석번호'] == arrangement[student])
            if not is_preferred_back_seat(seat):
                return -1000000
            score += 10
    
    return score

def generate_best_arrangement(students, seats, balance_students, separation_groups, front_priority, back_priority, iterations=2000):
    """최적 배치 생성"""
    best_score = -1e9
    best_arrangement = {}
    invalid_best_score = -1e9
    invalid_best_arrangement = {}
    
    student_names = [s['이름'] for s in students]
    fixed_arrangement, available_seats = assign_priority_students(seats, front_priority, back_priority)
    remaining_students = [name for name in student_names if name not in fixed_arrangement]
    available_seat_ids = list(available_seats)

    if not available_seat_ids:
        return fixed_arrangement

    for _ in range(iterations):
        shuffled = random.sample(available_seat_ids, len(available_seat_ids))
        arrangement = {**fixed_arrangement, **dict(zip(remaining_students, shuffled))}

        score = score_arrangement(arrangement, seats, balance_students, separation_groups, front_priority, back_priority)
        if score < -999000:
            if score > invalid_best_score:
                invalid_best_score = score
                invalid_best_arrangement = arrangement.copy()
            continue
        if score > best_score:
            best_score = score
            best_arrangement = arrangement.copy()

    if best_arrangement:
        return best_arrangement
    if invalid_best_arrangement:
        return invalid_best_arrangement
    return {**fixed_arrangement, **dict(zip(remaining_students, random.sample(available_seat_ids, len(available_seat_ids))))}

def render_seat_map(arrangement, seats):
    """좌석 배치 시각화"""
    # 분단별 그룹화
    groups = {}
    for seat in seats:
        group = seat['분단']
        if group not in groups:
            groups[group] = []
        groups[group].append(seat)
    
    cols = st.columns(len(groups))
    
    for i, (group, group_seats) in enumerate(groups.items()):
        with cols[i]:
            # 분단 제목을 먼저 표시
            st.markdown(f'<div class="group-header">{group}분단</div>', unsafe_allow_html=True)
            
            # 행별 정렬 (앞줄부터)
            sorted_seats = sorted(group_seats, key=lambda s: (s['행'], s['열']))
            
            # 세로 1렬로 표시
            rows = []
            for seat in sorted_seats:
                student = next((name for name, seat_num in arrangement.items() if seat_num == seat['좌석번호']), "")
                seat_class = "front-seat" if seat['앞줄'] else "back-seat" if seat['뒷줄'] else ""
                rows.append(f'<div class="seat-card {seat_class}">{student}</div>')
            
            st.markdown(''.join(rows), unsafe_allow_html=True)

# 단계별 UI 함수들


def step_1_students():
    st.markdown('<div class="step-header">1단계: 학생 명단 입력</div>', unsafe_allow_html=True)
    st.markdown("학생 명단을 불러와 볼까요?")
    
    input_method = st.radio("입력 방식 선택", ["직접 입력", "CSV 파일 업로드"], key="input_method")
    
    if input_method == "직접 입력":
        # 이전 입력값이 있으면 불러오기
        default_text = ""
        if st.session_state.students:
            default_text = "\n".join([f"{s['번호']} {s['이름']}" for s in st.session_state.students])
        
        text_input = st.text_area(
            "학생 명단을 입력하세요 (예: 1 김민준  2 박서연)",
            value=default_text,
            placeholder="1 박성진\n2 강영현\n3 김원필\n4 윤도운",
            height=150,
            key="student_text"
        )
        if text_input:
            df = parse_student_input(text_input)
            if not df.empty:
                st.success(f"{len(df)}명의 학생을 불러왔어요!")
                st.dataframe(df, use_container_width=True)
                if st.button("이 명단으로 진행", key="confirm_students"):
                    st.session_state.students = df.to_dict('records')
                    st.session_state.step = 2
                    st.rerun()
    
    else:  # CSV 업로드
        st.markdown("CSV 양식 파일을 다운로드하고, 아래 예시처럼 `번호`와 `이름`을 입력한 다음 업로드해 주세요.")
        csv_bytes = create_student_template_csv()
        st.download_button(
            "CSV 예시 양식 다운로드",
            data=csv_bytes,
            file_name="학생_명단_예시.csv",
            mime="text/csv"
        )
        uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=['csv'], key="student_csv")
        if uploaded_file:
            df = load_csv_file(uploaded_file)
            if not df.empty:
                st.success(f"{len(df)}명의 학생을 불러왔어요!")
                st.dataframe(df, use_container_width=True)
                if st.button("이 명단으로 진행", key="confirm_csv"):
                    st.session_state.students = df.to_dict('records')
                    st.session_state.step = 2
                    st.rerun()
    
    st.markdown("💡 **팁**: 한글(.hwp) 파일은 명렬표를 복사해 텍스트로 붙여넣거나 CSV로 저장해 업로드해 주세요.")

def step_2_seats():
    st.markdown('<div class="step-header">2단계: 자리 구조 입력</div>', unsafe_allow_html=True)
    st.markdown("교실 자리 구조를 설정해 주세요.")
    
    # 중앙 정렬을 위한 컬럼
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 이전 값이 있으면 불러오기
        default_num_groups = st.session_state.seat_layout['num_groups'] if st.session_state.seat_layout else 4
        num_groups = st.number_input("총 분단 수", min_value=1, max_value=10, value=default_num_groups, key="num_groups")
    
    st.markdown("---")
    
    # 분단 입력 필드는 전체 너비 사용
    seats_per_group = []
    cols = st.columns(num_groups)
    for i in range(num_groups):
        with cols[i]:
            # 이전 값이 있으면 불러오기
            default_seats = 5
            if st.session_state.seat_layout and i < len(st.session_state.seat_layout.get('seats_per_group', [])):
                default_seats = st.session_state.seat_layout['seats_per_group'][i]
            seats = st.number_input(f"{i+1}분단", min_value=1, max_value=20, value=default_seats, key=f"group_{i}")
            seats_per_group.append(seats)
    
    # 세션 상태에 저장
    st.session_state.seat_layout = {'num_groups': num_groups, 'seats_per_group': seats_per_group}
    
    st.markdown("---")
    
    # 정보 메시지는 전체 너비 사용
    total_seats = sum(seats_per_group)
    student_count = len(st.session_state.students)
    
    st.info(f"총 좌석 수: {total_seats}, 학생 수: {student_count}")
    
    if total_seats != student_count:
        st.warning("⚠️ 좌석 수와 학생 수가 맞지 않아요. 조정해 주세요.")
    else:
        st.success("✅ 좌석 구조가 설정되었습니다!")
        # 버튼은 중앙 정렬
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("다음 단계로", key="confirm_seats", use_container_width=True):
                st.session_state.seats = build_seat_layout(num_groups, seats_per_group)
                st.session_state.step = 3
                st.rerun()

def step_3_balance():
    st.markdown('<div class="step-header">3단계: 모둠별 리더 후보 학생</div>', unsafe_allow_html=True)
    st.markdown("👥 **각 모둠별로 1명씩 들어가면 좋을 학생들**을 입력하세요. (예: 모둠활동 시 리더 역할을 할 학생, 성적 우수 학생 등)")
    st.markdown("✨ 이 학생들은 가능한 서로 다른 분단에 분산 배치됩니다.")
    
    # 이전 입력값이 있으면 불러오기
    default_text = ""
    if 'balance_text_input' in st.session_state and st.session_state.balance_text_input:
        default_text = st.session_state.balance_text_input
    
    balance_input = st.text_area(
        "학생 이름 입력 (쉼표로 구분)",
        value=default_text,
        placeholder="박성진, 강영현, 김원필, 윤도운",
        key="balance_text"
    )
    
    # 세션 상태에 저장
    st.session_state.balance_text_input = balance_input
    
    if balance_input:
        names = [name.strip() for name in balance_input.split(',') if name.strip()]
        valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
        invalid_names = [name for name in names if name not in valid_names]
        
        if invalid_names:
            st.warning(f"명단에 없는 이름: {', '.join(invalid_names)}")
        
        if valid_names:
            st.success(f"균형 배치 학생 {len(valid_names)}명 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_balance"):
            st.session_state.balance_students = []
            st.session_state.step = 4
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_balance"):
            if balance_input:
                names = [name.strip() for name in balance_input.split(',') if name.strip()]
                st.session_state.balance_students = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
            st.session_state.step = 4
            st.rerun()

def step_4_separation():
    st.markdown('<div class="step-header">4단계: 분리 배치 학생 세트</div>', unsafe_allow_html=True)
    st.markdown("**✨ 같은 분단에 배치하지 말아야 할 학생 세트**를 입력하세요.")
    st.markdown(" 입력된 학생들은 서로 다른 분단에 배치되며, 가능한 서로 가장 먼 자리로 배치됩니다.")
    st.markdown("📝 **입력 예시:**")
    st.markdown("- 한 줄에 한 세트씩 입력")
    st.markdown("- 세트 설정은 **띄어쓰기, 쉼표, 하이픈(-)** 중 아무거나 사용해서 설정 가능")
    st.markdown("- 예시 1: 박성진 강영현 (띄어쓰기)")
    st.markdown("- 예시 2: 김원필, 윤도운 (쉼표)")
    st.markdown("- 예시 3: 박성진 - 윤도운 (하이픈)")
    
    # 이전 입력값이 있으면 불러오기
    default_text = ""
    if 'separation_text_input' in st.session_state and st.session_state.separation_text_input:
        default_text = st.session_state.separation_text_input
    
    separation_input = st.text_area(
        "세트별로 한 줄씩 입력",
        value=default_text,
        placeholder="박성진 강영현\n김원필, 윤도운",
        height=100,
        key="separation_text"
    )
    
    # 세션 상태에 저장
    st.session_state.separation_text_input = separation_input
    
    groups = []
    if separation_input:
        lines = separation_input.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 다양한 구분자 처리
            names = re.split(r'[,\-\s/]+', line)
            names = [name.strip() for name in names if name.strip()]
            if names:
                valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
                if valid_names:
                    groups.append(valid_names)
        
        st.success(f"분리 배치 세트 {len(groups)}개 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_separation"):
            st.session_state.separation_groups = []
            st.session_state.step = 5
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_separation"):
            if separation_input:
                lines = separation_input.strip().split('\n')
                groups = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    names = re.split(r'[,\-\s/]+', line)
                    names = [name.strip() for name in names if name.strip()]
                    valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
                    if valid_names:
                        groups.append(valid_names)
                st.session_state.separation_groups = groups
            st.session_state.step = 5
            st.rerun()

def step_5_front_priority():
    st.markdown('<div class="step-header">5단계: 앞줄 우선 학생</div>', unsafe_allow_html=True)
    st.markdown("👩‍🏫 각 분단의 **1번째~2번째 줄 이내에 배치하면 좋을 학생들**을 입력하세요. (예: 시력이 나쁜 학생, 키가 작은 학생 등)")
    st.markdown("✨ 입력된 학생은 최대한 앞쪽으로 배치합니다.")
    
    # 이전 입력값이 있으면 불러오기
    default_text = ""
    if 'front_text_input' in st.session_state and st.session_state.front_text_input:
        default_text = st.session_state.front_text_input
    
    front_input = st.text_area(
        "학생 이름 입력 (쉼표로 구분)",
        value=default_text,
        placeholder="김민준, 박서연",
        key="front_text"
    )
    
    # 세션 상태에 저장
    st.session_state.front_text_input = front_input
    
    if front_input:
        names = [name.strip() for name in front_input.split(',') if name.strip()]
        valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
        if valid_names:
            st.success(f"앞줄 우선 학생 {len(valid_names)}명 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_front"):
            st.session_state.front_priority = []
            st.session_state.front_text_input = ""
            st.session_state.step = 6
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_front"):
            if front_input:
                names = [name.strip() for name in front_input.split(',') if name.strip()]
                st.session_state.front_priority = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
            st.session_state.step = 6
            st.rerun()

def step_6_back_priority():
    st.markdown('<div class="step-header">6단계: 뒷줄 우선 학생</div>', unsafe_allow_html=True)
    st.markdown("👩‍🏫 각 분단의 **4번째~5번째 줄에 배치하면 좋을 학생들**을 입력하세요. (예: 키가 큰 학생, 선생님으로부터 멀리 떨어져 있게 하고 싶은 학생 등)")
    st.markdown("✨ 입력된 학생은 최대한 뒤쪽 자리에 배치합니다.")
    
    # 이전 입력값이 있으면 불러오기
    default_text = ""
    if 'back_text_input' in st.session_state and st.session_state.back_text_input:
        default_text = st.session_state.back_text_input
    
    back_input = st.text_area(
        "학생 이름 입력 (쉼표로 구분)",
        value=default_text,
        placeholder="이도윤, 최민수",
        key="back_text"
    )
    
    # 세션 상태에 저장
    st.session_state.back_text_input = back_input
    
    if back_input:
        names = [name.strip() for name in back_input.split(',') if name.strip()]
        valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
        if valid_names:
            st.success(f"뒷줄 우선 학생 {len(valid_names)}명 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_back"):
            st.session_state.back_priority = []
            st.session_state.back_text_input = ""
            st.session_state.step = 7
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_back"):
            if back_input:
                names = [name.strip() for name in back_input.split(',') if name.strip()]
                st.session_state.back_priority = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
            st.session_state.step = 7
            st.rerun()

def step_7_generate():
    st.markdown('<div class="step-header">7단계: 자리 배정 실행</div>', unsafe_allow_html=True)
    st.markdown("🫡 입력하신 조건을 반영하여 최적의 자리 배치를 생성합니다.")
    
    # 조건 요약
    st.markdown("📋 **입력된 조건 요약:**")
    st.write(f"- 모둠 균형 배치 학생: {len(st.session_state.balance_students)}명")
    st.write(f"- 분리 배치 세트: {len(st.session_state.separation_groups)}개")
    st.write(f"- 앞줄 우선 학생: {len(st.session_state.front_priority)}명")
    st.write(f"- 뒷줄 우선 학생: {len(st.session_state.back_priority)}명")
    
    if st.button("자리 배정 시작", key="generate"):
        with st.spinner("최적 배치를 찾는 중..."):
            arrangement = generate_best_arrangement(
                st.session_state.students,
                st.session_state.seats,
                st.session_state.balance_students,
                st.session_state.separation_groups,
                st.session_state.front_priority,
                st.session_state.back_priority
            )
            st.session_state.arrangement = arrangement
            st.session_state.arrangement_version += 1
            st.session_state.step = 8
            st.rerun()


def step_8_result():
    st.markdown('<div class="step-header">8단계: 결과 확인 및 수정</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### 📍 자리 배치 결과")
    with col2:
        if st.button("다시 배치하기", key="reshuffle"):
            arrangement = generate_best_arrangement(
                st.session_state.students,
                st.session_state.seats,
                st.session_state.balance_students,
                st.session_state.separation_groups,
                st.session_state.front_priority,
                st.session_state.back_priority
            )
            st.session_state.arrangement = arrangement
            st.session_state.arrangement_version += 1
            st.rerun()

    render_seat_map(st.session_state.arrangement, st.session_state.seats)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### ✏️ 직접 수정")
    st.markdown("마음에 들지 않는 부분이 있다면 직접 수정하세요.")
    
    # 수정 방식 선택
    edit_mode = st.radio("수정 방식", ["좌석별 학생 변경", "학생 자리 교환"], key="edit_mode")
    
    if edit_mode == "좌석별 학생 변경":
        st.markdown("각 좌석의 학생을 선택하세요:")
        groups = {}
        for seat in st.session_state.seats:
            groups.setdefault(seat['분단'], []).append(seat)
        cols = st.columns(len(groups))
        for i, (group, group_seats) in enumerate(sorted(groups.items())):
            with cols[i]:
                st.markdown(f"#### {group}분단")
                for seat in sorted(group_seats, key=lambda s: (s['행'], s['열'])):
                    current_student = next((name for name, seat_num in st.session_state.arrangement.items() if seat_num == seat['좌석번호']), "")
                    options = [""] + [s['이름'] for s in st.session_state.students]
                    try:
                        default_index = options.index(current_student) if current_student else 0
                    except ValueError:
                        default_index = 0
                    new_student = st.selectbox(
                        f"좌석 {seat['좌석번호']} ({group}분단)",
                        options,
                        index=default_index,
                        key=f"seat_{seat['좌석번호']}_{st.session_state.arrangement_version}"
                    )
                    if new_student and new_student != current_student:
                        if current_student and current_student in st.session_state.arrangement:
                            del st.session_state.arrangement[current_student]
                        st.session_state.arrangement[new_student] = seat['좌석번호']
    else:  # 학생 자리 교환
        st.markdown("교환할 두 학생을 선택하세요:")
        col1, col2 = st.columns(2)
        with col1:
            student1 = st.selectbox("첫 번째 학생", [s['이름'] for s in st.session_state.students], key="swap1")
        with col2:
            student2 = st.selectbox("두 번째 학생", [s['이름'] for s in st.session_state.students], key="swap2")
        
        if student1 and student2 and student1 != student2:
            if st.button("자리 교환", key="swap"):
                seat1 = st.session_state.arrangement[student1]
                seat2 = st.session_state.arrangement[student2]
                st.session_state.arrangement[student1] = seat2
                st.session_state.arrangement[student2] = seat1
                st.success("자리 교환이 완료되었습니다!")
                st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("최종 자리 확정", key="finalize", use_container_width=True):
        st.session_state.student_random_ready = False
        st.session_state.step = 9
        st.rerun()
    st.markdown("**✨ 위 버튼을 누르면 학생용 화면으로 이동합니다. 선생님께서 학생들의 성향과 여러 배치 조건을 고려해 미리 배정한 결과이지만, 학생들에게는 마치 랜덤으로 배정된 것처럼 보이게 됩니다.**")


def step_9_student_preview():
    st.markdown('<div class="step-header">9단계: 학생용 랜덤 자리 배정</div>', unsafe_allow_html=True)
    st.markdown("🎉 반 학생 명단을 확인한 후 아래 버튼을 눌러 랜덤 자리 배정 결과를 확인해 보세요!")
    
    student_names = [s['이름'] for s in st.session_state.students]
    items = ''.join([f"<div class='student-name'>{i+1}. {name}</div>" for i, name in enumerate(student_names)])
    st.markdown(
        f"<div class='student-list-box'><p>❤️학생 명단</p>{items}</div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("랜덤 자리 배정하기", key="student_random", use_container_width=True):
        with st.spinner("자리 배정 중..."):
            time.sleep(3)
        st.session_state.student_random_ready = True
        st.session_state.step = 9
        st.rerun()

    if st.session_state.student_random_ready:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎲 랜덤 배정 결과")
        render_seat_map(st.session_state.arrangement, st.session_state.seats)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("다시 배정하기", key="student_reshuffle", use_container_width=True):
            arrangement = generate_best_arrangement(
                st.session_state.students,
                st.session_state.seats,
                st.session_state.balance_students,
                st.session_state.separation_groups,
                st.session_state.front_priority,
                st.session_state.back_priority
            )
            st.session_state.arrangement = arrangement
            st.session_state.arrangement_version += 1
            st.session_state.student_random_ready = True
            st.rerun()

# 이전 단계 및 처음으로 버튼
if st.session_state.step > 0:
    col_prev, col_spacer, col_home = st.columns([2, 6, 2])
    with col_prev:
        if st.button("◀ 이전 단계", key="prev", use_container_width=True):
            st.session_state.step -= 1
            st.rerun()
    with col_home:
        if st.button("처음으로", key="home", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

# 단계별 UI 호출
if st.session_state.step == 1:
    step_1_students()
elif st.session_state.step == 2:
    step_2_seats()
elif st.session_state.step == 3:
    step_3_balance()
elif st.session_state.step == 4:
    step_4_separation()
elif st.session_state.step == 5:
    step_5_front_priority()
elif st.session_state.step == 6:
    step_6_back_priority()
elif st.session_state.step == 7:
    step_7_generate()
elif st.session_state.step == 8:
    step_8_result()
elif st.session_state.step == 9:
    step_9_student_preview()

# 사용 안내
st.markdown("---")
st.markdown("**사용 안내:** 이 앱은 초등학교 학급 자리 바꾸기를 돕기 위해 만들어졌습니다. 단계별로 입력하시면 최적의 배치를 자동 생성해 드려요. 결과가 마음에 들지 않으면 직접 수정할 수도 있어요!")
