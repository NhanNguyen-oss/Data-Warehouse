# Profiling report (stage S2)

File này do `python src/etl/profiling.py` sinh ra. Không sửa tay; chạy lại để cập nhật.

- run_id: `cb356a9e873c`, xong lúc 2026-10-09T17:12:46+00:00, 13.6 giây, Python 3.12.3
- Bộ lọc năm: 2021, 2022, 2023, 2024, 2025
- Nguồn (sha256):
  - `data/raw/dft-road-casualty-statistics-collision-last-5-years.csv` `06a03c0e5504175e23ed98e3e0b4767ac61d396c073405a1bddab9339c18f948`
  - `data/raw/traffic/dft_traffic_counts_aadf.zip` `5273cf63da4ca8b317bfe972d8a345e7932db0fff7a7789998a890f0081232b6`
  - `data/raw/traffic/count_points.zip` `4772abb13761694f35c7aba6d83915c5c168e94a0d25ae401e4b7e84ef7fcff2`
  - `data/raw/traffic/local_authority_traffic.csv` `058a61b9f6f7d07a9363c339829c6723fdecc4270f500611d1790eae6da7b9fc`

## STATS19 collision

- Tổng bản ghi 513.801, trong phạm vi năm 513.801.
- `collision_index`: 513.801 giá trị duy nhất, 0 trùng, 0 rỗng.
- Ngày không đọc được 0; năm của `date` khác `collision_year` 0; giờ không đọc được 0.
- Tọa độ thiếu 53, nằm ngoài khung GB 0.
- Highway authority thiếu 53; dòng có `local_authority_highway` khác `_current` 7.615.

| Năm | Vụ | Fatal | Serious | Slight | Severe share % | Injury-based % | Highway authority (current) |
|---|---|---|---|---|---|---|---|
| 2021 | 101.087 | 1.474 | 21.284 | 78.329 | 22,51 | 49,62 | 206 |
| 2022 | 106.004 | 1.602 | 23.333 | 81.069 | 23,52 | 52,57 | 207 |
| 2023 | 104.258 | 1.522 | 23.438 | 79.298 | 23,94 | 53,73 | 207 |
| 2024 | 100.927 | 1.502 | 23.567 | 75.858 | 24,84 | 58,75 | 207 |
| 2025 | 101.525 | 1.453 | 25.191 | 74.881 | 26,24 | 86,53 | 207 |

Severe share theo collision severity bị ảnh hưởng bởi việc chuyển sang hệ thống ghi nhận dựa trên thương tích (cột Injury-based). Không so sánh giữa các năm nếu chưa hiệu chỉnh.

Cột có tỷ lệ rỗng hoặc `-1` cao nhất (trong phạm vi năm):

| Cột | Số dòng | % |
|---|---|---|
| `local_authority_district` | 513.607 | 99,96 |
| `junction_control` | 217.897 | 42,41 |
| `enhanced_severity_collision` | 204.752 | 39,85 |
| `second_road_number` | 178.098 | 34,66 |
| `special_conditions_at_site` | 151.370 | 29,46 |
| `carriageway_hazards_historic` | 151.367 | 29,46 |
| `pedestrian_crossing_human_control_historic` | 150.889 | 29,37 |
| `pedestrian_crossing_physical_facilities_historic` | 150.860 | 29,36 |
| `junction_detail_historic` | 147.476 | 28,70 |
| `trunk_road_flag` | 36.318 | 7,07 |
| `lsoa_of_accident_location` | 20.587 | 4,01 |
| `junction_detail` | 19.982 | 3,89 |

London (local_authority_highway starts with E09): 111.335 vụ trong phạm vi năm, 33 authority theo mã current.

| Năm | Vụ (mã lúc xảy ra) | Vụ (mã current) |
|---|---|---|
| 2021 | 23.127 | 23.138 |
| 2022 | 23.477 | 23.502 |
| 2023 | 22.895 | 22.914 |
| 2024 | 20.967 | 21.000 |
| 2025 | 20.869 | 20.901 |

## DfT AADF

- Tổng bản ghi 600.551 (năm 2000–2025), 46.754 count point; trong phạm vi năm 111.465.
- Khóa (`count_point_id`, `year`): 0 trùng trên toàn file.
- Estimated chiếm 64,38% bản ghi trong phạm vi năm.
- `link_length_km` thiếu hoặc ≤ 0: 21.989 bản ghi (19,73%) trong phạm vi năm; 134.684 (22,43%) trên toàn file.
- Thành phần không cộng ra `all_motor_vehicles`: 49.297 (phân bố `all_motor_vehicles` − tổng thành phần: -2: 857, -1: 24.227, 1: 23.419, 2: 794); HGV con không cộng ra `all_HGVs`: 48.595; `all_motor_vehicles` = 0: 19.
- Count point có mặt ở mọi năm trong phạm vi: 21.201; count point đổi mã authority giữa các năm (toàn file): 267.

| Năm | Bản ghi | Count point | Estimated % | Link length thiếu (Major) | Link length thiếu (Minor) | Authority |
|---|---|---|---|---|---|---|
| 2021 | 22.297 | 22.297 | 62,67 | 0,00% | 100,00% | 207 |
| 2022 | 22.240 | 22.240 | 63,76 | 0,00% | 100,00% | 206 |
| 2023 | 22.257 | 22.257 | 66,06 | 0,00% | 100,00% | 208 |
| 2024 | 22.337 | 22.337 | 65,01 | 0,00% | 100,00% | 207 |
| 2025 | 22.334 | 22.334 | 64,40 | 0,00% | 100,00% | 207 |

London (local_authority_code starts with E09): 10.207 bản ghi, Estimated 64,54%, link length thiếu 10,53%, 1.977 count point có mặt mọi năm. Dòng mà mã E09 và `region_name = London` không khớp: 0.

Phương pháp ước tính chi tiết (trong phạm vi năm):

- Estimated using AADF from previous year on this link: 66.686
- Manual count: 32.991
- Estimated from nearby links: 5.076
- Automatic counter: 4.860
- Dependent on a neighbouring counted link: 1.479
- Dependent on an automatic counter on a neighbouring link: 373

## Count points và local authority traffic

- `count_points.csv`: 46.754 dòng, 0 `count_point_id` trùng, năm metadata 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025; link length thiếu 53,01%.
- AADF count point không có trong `count_points.csv`: 0; count point không có AADF: 0.
- `local_authority_traffic.csv`: 6.767 dòng, năm 1993–2025, khóa (`local_authority_code`, `year`) trùng 0; giá trị thiếu trong phạm vi năm: không có; dòng ghi số dạng khoa học (ví dụ `1.245e+09`): 1.318.

## Đối chiếu mã authority giữa ba nguồn

Năm chung: 2021, 2022, 2023, 2024, 2025.

STATS19 dùng `local_authority_highway_current`:

| Năm | STATS19 | AADF | LA traffic | STATS19 thiếu trong AADF | AADF thiếu trong STATS19 | STATS19 thiếu trong LA traffic | LA traffic thiếu trong STATS19 | London khớp cả ba / 33 |
|---|---|---|---|---|---|---|---|---|
| 2021 | 206 | 207 | 206 | E06000063, E06000064, E08000038, E08000039 | E06000053, E08000016, E08000019, E10000006, E10000021 | E06000063, E06000064, E08000038, E08000039 | E06000053, E08000016, E08000019, E10000006 | 33 |
| 2022 | 207 | 206 | 206 | E06000063, E06000064, E08000038, E08000039 | E08000016, E08000019, E10000006 | E06000063, E06000064, E08000038, E08000039 | E08000016, E08000019, E10000006 | 33 |
| 2023 | 207 | 208 | 207 | E08000038, E08000039 | E08000016, E08000019, E10000006 | E08000038, E08000039 | E08000016, E08000019 | 33 |
| 2024 | 207 | 207 | 207 | E08000038, E08000039 | E08000016, E08000019 | E08000038, E08000039 | E08000016, E08000019 | 33 |
| 2025 | 207 | 207 | 207 | E08000038, E08000039 | E08000016, E08000019 | E08000038, E08000039 | E08000016, E08000019 | 33 |

STATS19 dùng `local_authority_highway` (mã lúc xảy ra vụ):

| Năm | STATS19 | AADF | LA traffic | STATS19 thiếu trong AADF | AADF thiếu trong STATS19 | STATS19 thiếu trong LA traffic | LA traffic thiếu trong STATS19 | London khớp cả ba / 33 |
|---|---|---|---|---|---|---|---|---|
| 2021 | 206 | 207 | 206 | EHEATHROW | E06000053, E10000021 | EHEATHROW | E06000053 | 33 |
| 2022 | 207 | 206 | 206 | EHEATHROW | — | EHEATHROW | — | 33 |
| 2023 | 208 | 208 | 207 | EHEATHROW | E10000006 | EHEATHROW | — | 33 |
| 2024 | 208 | 207 | 207 | EHEATHROW | — | EHEATHROW | — | 33 |
| 2025 | 208 | 207 | 207 | E08000038, E08000039, EHEATHROW | E08000016, E08000019 | E08000038, E08000039, EHEATHROW | E08000016, E08000019 | 33 |

## Trạng thái bản phát hành

- STATS19: Không xác định được từ file: data guide không ghi provisional/final. README ghi bản 'last 5 years' chính thức cho 2025; cần đối chiếu trang DfT.
- Traffic: Không xác định được từ file; member trong zip ghi ngày 2026-06-02. Cần đối chiếu trang roadtraffic.dft.gov.uk.
