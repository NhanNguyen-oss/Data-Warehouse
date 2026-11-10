"""Interactive DSS over the same filtered warehouse aggregates as the dashboard."""
from pathlib import Path
import sys
from math import isclose
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dss.authority import DEFAULT_WEIGHTS, LABELS, prepare_authorities
from dss.model import Criterion, DecisionSupportModel

CRITERIA = {'mean_ksi': 'KSI hiệu chỉnh trung bình năm', 'ksi_change_pct': 'Thay đổi KSI (%)',
            'ksi_share_pct': 'Tỷ trọng KSI hiệu chỉnh (%)'}
REASONS = {
    'Missing or duplicate authority-month groups.': 'Thiếu hoặc trùng nhóm địa bàn–tháng.',
    'Incomplete severity adjustments.': 'Thiếu số hiệu chỉnh mức độ nghiêm trọng.',
    'Invalid casualty or KSI totals.': 'Tổng số nạn nhân hoặc KSI không hợp lệ.',
    'No casualty denominator.': 'Không có nạn nhân để làm mẫu số.',
    'Zero baseline KSI; percentage change is undefined.':
        'KSI năm gốc bằng 0; không xác định được phần trăm thay đổi.',
}
COLUMNS = {
    'year': 'Năm', 'month_number': 'Tháng', 'authority_code': 'Mã địa bàn',
    'authority_name': 'Địa bàn', 'collisions': 'Số vụ va chạm', 'casualties': 'Số nạn nhân',
    'fatalities': 'Số tử vong', 'ksi_adjusted': 'KSI hiệu chỉnh',
    'adjustment_missing': 'Nạn nhân thiếu hiệu chỉnh', 'reason': 'Lý do loại',
    'first_year_ksi': 'KSI năm đầu', 'last_year_ksi': 'KSI năm cuối', **CRITERIA,
    **{key + '_contribution': 'Đóng góp: ' + label for key, label in CRITERIA.items()},
    'rank': 'Hạng', 'score': 'Điểm', 'recommended': 'Đề xuất',
    'rank_baseline': 'Hạng (mặc định)', 'rank_gain': 'Thay đổi hạng',
    'score_baseline': 'Điểm (mặc định)', 'recommended_baseline': 'Đề xuất (mặc định)',
}


def column_labels(frame):
    return {column: COLUMNS[column] for column in frame.columns if column in COLUMNS}


def ranking_table(result, details, top_n, threshold):
    rows = []
    rank, previous = 0, None
    for position, (code, score) in enumerate(result.ranking, 1):
        if previous is None or not isclose(score, previous, abs_tol=1e-12):
            rank = position
        previous = score
        rows.append({**details[code], 'rank': rank, 'score': score,
                     'recommended': rank <= top_n and score >= threshold and score > 1e-12,
                     **{key + '_contribution': result.contributions[code].get(key, 0.)
                        for key in LABELS}})
    return pd.DataFrame(rows)


def render_dss(view, years):
    st.header('Hỗ trợ ra quyết định · Ưu tiên địa bàn')
    st.caption('Xếp hạng ưu tiên khảo sát an toàn giao thông cho các địa bàn theo năm và địa bàn đang chọn. '
               'Điểm chỉ mang tính tương đối để so sánh, không dự báo hiệu quả can thiệp.')
    has_trend = len(set(years)) > 1
    defaults = {**DEFAULT_WEIGHTS, 'ksi_change_pct': DEFAULT_WEIGHTS['ksi_change_pct'] if has_trend else 0}
    with st.expander('Tiêu chí và giả định'):
        st.markdown('''| Tiêu chí | Cách đo | Mặc định thăm dò | Mục đích |
| --- | --- | --- | --- |
| KSI hiệu chỉnh trung bình năm | KSI hiệu chỉnh mức nạn nhân / số năm đã chọn | 50 | Nhấn mạnh gánh nặng thương tích nặng |
| Thay đổi KSI (%) | (Năm cuối đã chọn / năm đầu đã chọn − 1) × 100 | 30 | Nhấn mạnh xu hướng xấu đi |
| Tỷ trọng KSI hiệu chỉnh (%) | KSI hiệu chỉnh / tổng số nạn nhân × 100 | 20 | Nhấn mạnh cơ cấu mức độ nghiêm trọng |

Giá trị càng cao thì mức ưu tiên càng cao. Trọng số được chuẩn hóa để tổng bằng 1. Giá trị mặc định chỉ để
thăm dò, không phải trọng số chính sách đã hiệu chỉnh. Gánh nặng KSI và tỷ trọng KSI có liên quan với nhau;
hãy kiểm tra độ nhạy theo trọng số. Chuẩn hóa min-max dựa trên các địa bàn hợp lệ đang được chọn. Tiêu chí
không đổi giữa các địa bàn có đóng góp bằng 0. Thay đổi tập so sánh có thể làm thay đổi điểm. Một địa bàn
đơn lẻ không thể xếp hạng so sánh. Chỉ các năm đã chọn có đủ 12 tháng và đủ số hiệu chỉnh mới hợp lệ. Mẫu số
bằng 0 và phần trăm thay đổi không xác định bị loại và được liệt kê. Dữ liệu thiếu không bao giờ được thay
bằng dữ liệu demo. Tỷ lệ theo lưu lượng (exposure) và dân số chưa được tích hợp vào kho. Các địa bàn đồng
điểm có cùng hạng và có thể làm số đề xuất vượt quá top N đã yêu cầu.''')
    if not has_trend:
        st.info('Chọn ít nhất hai năm để so sánh xu hướng. Trọng số xu hướng bằng 0 khi chỉ chọn một năm.')
    cols = st.columns(3)
    weights = {}
    for col, key in zip(cols, LABELS):
        weights[key] = col.slider('Trọng số ' + CRITERIA[key], 0, 100, defaults[key],
                                  disabled=key == 'ksi_change_pct' and not has_trend,
                                  key='dss_weight_' + key + ('_single' if not has_trend else '_multi'))
    threshold = st.slider('Điểm ưu tiên tối thiểu', 0.0, 1.0, 0.0, 0.05, key='dss_threshold')
    top_n = st.number_input('Số địa bàn đề xuất (tính cả đồng hạng)', min_value=1, max_value=33,
                            value=5, step=1, key='dss_top_n')
    if not sum(weights.values()):
        st.warning('Hãy đặt ít nhất một trọng số lớn hơn 0.')
        return
    alternatives, details, excluded = prepare_authorities(view.to_dict('records'), years)
    if excluded:
        st.warning(f'{len(excluded)} địa bàn bị loại do không đạt kiểm tra dữ liệu.')
        excluded_table = pd.DataFrame(excluded)
        excluded_table['reason'] = excluded_table.reason.map(lambda reason: REASONS.get(reason, reason))
        st.dataframe(excluded_table, hide_index=True, width="stretch",
                     column_config=column_labels(excluded_table))
    if len(alternatives) < 2:
        st.info('Cần ít nhất hai địa bàn có đủ dữ liệu các năm đã chọn để đưa ra đề xuất so sánh.')
        return
    model = DecisionSupportModel([Criterion(key, value) for key, value in weights.items()], threshold)
    result = model.recommend(alternatives)
    current = ranking_table(result, details, top_n, threshold)
    baseline_model = DecisionSupportModel([Criterion(key, value) for key, value in defaults.items()])
    baseline = ranking_table(baseline_model.recommend(alternatives), details, top_n, 0)
    comparison = current.merge(baseline[['authority_code', 'rank', 'score', 'recommended']],
                               on='authority_code', suffixes=('', '_baseline'))
    comparison['rank_gain'] = comparison.rank_baseline - comparison['rank']
    comparison['selected_years'] = ','.join(map(str, sorted(set(years))))
    comparison['threshold'] = threshold
    comparison['top_n'] = top_n
    for key, value in weights.items():
        comparison['weight_' + key] = value / sum(weights.values())
    st.caption('Trọng số thực tế: ' + ', '.join(f'{CRITERIA[k]} {v/sum(weights.values()):.0%}'
                                               for k, v in weights.items()))
    selected = current[current.recommended]
    if selected.empty:
        st.info('Không có địa bàn nào đạt ngưỡng với điểm so sánh dương.')
    else:
        st.success('Đề xuất ưu tiên khảo sát: ' + ', '.join(selected.authority_name))
        leader = current.iloc[0]
        parts = result.contributions[leader.authority_code]
        strongest = max(parts, key=parts.get)
        tie = (f'{len(result.tied)} địa bàn đồng hạng nhất.' if len(result.tied) > 1
               else 'Một địa bàn đứng đầu.')
        st.write(f"{leader.authority_name}: điểm {leader.score:.4f}; tiêu chí đóng góp nhiều nhất là "
                 f"{CRITERIA[strongest]} ({parts[strongest]:.4f} điểm). {tie}")
    st.subheader('Xếp hạng và đóng góp của từng tiêu chí')
    st.dataframe(current, hide_index=True, width="stretch", column_config=column_labels(current))
    st.subheader('So sánh what-if với trọng số mặc định')
    changed = int((comparison['rank'] != comparison.rank_baseline).sum())
    selection_changes = int((comparison.recommended != comparison.recommended_baseline).sum())
    st.write(f'{changed} địa bàn thay đổi hạng; {selection_changes} địa bàn thay đổi trạng thái đề xuất. '
             'Phương án gốc dùng trọng số mặc định và ngưỡng 0 trên cùng tập địa bàn hợp lệ.')
    shown = comparison[['authority_name', 'rank_baseline', 'rank', 'rank_gain',
                        'score_baseline', 'score', 'recommended_baseline', 'recommended']]
    st.dataframe(shown, hide_index=True, width="stretch", column_config=column_labels(shown))
    st.download_button('Tải kết quả so sánh DSS', comparison.to_csv(index=False).encode('utf-8-sig'),
                       'london_dss_comparison.csv', 'text/csv')
