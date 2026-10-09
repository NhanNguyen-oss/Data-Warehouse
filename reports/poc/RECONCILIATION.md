# Authority–year integration PoC (stage S3)

File này do `python src/etl/authority_year.py` sinh ra. Không sửa tay; chạy lại để cập nhật.

- run_id: `e26cba7767d5`, xong lúc 2026-10-09T17:18:19+00:00, 8.7 giây
- Năm: 2021, 2022, 2023, 2024, 2025
- Nguồn (sha256):
  - `data/raw/dft-road-casualty-statistics-collision-last-5-years.csv` `06a03c0e5504175e23ed98e3e0b4767ac61d396c073405a1bddab9339c18f948`
  - `data/raw/traffic/dft_traffic_counts_aadf.zip` `5273cf63da4ca8b317bfe972d8a345e7932db0fff7a7789998a890f0081232b6`
  - `data/raw/traffic/local_authority_traffic.csv` `058a61b9f6f7d07a9363c339829c6723fdecc4270f500611d1790eae6da7b9fc`

## Phương pháp

1. Mỗi nguồn được aggregate riêng về (authority_code, year), sau đó full outer join theo khóa này. Không có join collision × count point nên không có fan-out.
2. Mã chuẩn là mã authority của DfT Traffic trong năm đó (danh sách trong `local_authority_traffic.csv`).
3. Collision dùng `local_authority_highway` (mã lúc xảy ra vụ), áp `data/reference/authority_code_map.csv`.
4. Dòng AADF có mã không hợp lệ trong năm được gán mã của cùng count point ở năm sau gần nhất (`count_point_later_code`).
5. `aadf_mean_all_motor_vehicles` là trung bình của các count point được quan sát/ước tính, không phải lưu lượng toàn địa bàn.
6. `aadf_major_vehicle_km` = Σ AADF × `link_length_km` × số ngày của năm (366 cho 2024), chỉ Major roads vì Minor không có link length.
7. `la_vehicle_km` = vehicle miles toàn mạng trong `local_authority_traffic.csv` × 1,609344.
8. Cột `candidate_*` là rate thử nghiệm để kiểm tra tính khả thi, **chưa bật** cho dashboard/DSS (D05, D07).

## Đối soát

| Kiểm tra | Raw | Output | Kết quả |
|---|---|---|---|
| Khóa (authority_code, year) trùng | — | 0 | OK |
| Collisions | 513.801 | 513.801 | OK |
| AADF rows | 111.465 | 111.465 | OK |
| LA traffic rows | 1.033 | 1.033 | OK |
| Authority–year có mã hợp lệ | 1.033 | 1.033 | OK |
| Collisions không ghép được mã | — | 0 | OK |
| AADF rows không ghép được mã | — | 0 | OK |
| Major vehicle-km AADF > vehicle-km toàn mạng | — | 0 | OK |

Độ bao phủ (authority–year có mã hợp lệ nhưng thiếu một nguồn):

- Thiếu collisions: E06000053 2021
- Thiếu AADF: không có
- Thiếu LA traffic: không có
- Major vehicle-km AADF vượt toàn mạng: không có

## Đổi mã (remap audit)

| Nguồn | Năm | Mã gốc | Mã chuẩn | Phương pháp | Số dòng |
|---|---|---|---|---|---|
| aadf | 2021 | E10000021 | E06000062 | count_point_later_code | 1 |
| aadf | 2023 | E10000006 | E06000063 | count_point_later_code | 5 |
| aadf | 2023 | E10000006 | E06000064 | count_point_later_code | 5 |
| stats19 | 2021 | EHEATHROW | E09000017 | authority_code_map | 12 |
| stats19 | 2022 | EHEATHROW | E09000017 | authority_code_map | 25 |
| stats19 | 2023 | EHEATHROW | E09000017 | authority_code_map | 19 |
| stats19 | 2024 | EHEATHROW | E09000017 | authority_code_map | 33 |
| stats19 | 2025 | E08000038 | E08000016 | authority_code_map | 364 |
| stats19 | 2025 | E08000039 | E08000019 | authority_code_map | 838 |
| stats19 | 2025 | EHEATHROW | E09000017 | authority_code_map | 30 |

## London (33 authority, mã E09)

| Năm | Authority | Collisions | Fatal + serious | Adjusted KSI collisions | Injury-based % | AADF count points | Estimated % | Major vehicle-km (tỷ) | Vehicle-km toàn mạng (tỷ) | Candidate collisions / 100M vkm |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | 33 | 23.139 | 3.483 | 3483,40 | 0,67 | 2.038 | 64,18 | 17,24 | 29,70 | 77,92 |
| 2022 | 33 | 23.502 | 3.826 | 3826,30 | 0,78 | 2.037 | 65,19 | 18,19 | 30,72 | 76,50 |
| 2023 | 33 | 22.914 | 3.600 | 3600,00 | 0,83 | 2.039 | 64,10 | 18,27 | 30,89 | 74,17 |
| 2024 | 33 | 21.000 | 3.602 | 3602,20 | 0,86 | 2.043 | 65,30 | 18,37 | 31,27 | 67,15 |
| 2025 | 33 | 20.899 | 3.854 | 3854,00 | 90,71 | 2.050 | 63,95 | 18,46 | 31,62 | 66,09 |

## Giới hạn của PoC

- Grain năm; không kết luận về giờ cao điểm hay tắc nghẽn.
- Cumbria tách thành Cumberland và Westmorland and Furness từ 2023; chuỗi thời gian của ba mã này gãy tại 2023. Cần version history trong `dim_authority` (SCD Type 2) nếu muốn so sánh xuyên năm.
- STATS19 chỉ gồm vụ có người bị thương được cảnh sát ghi nhận (under-reporting).
- Severe share chịu ảnh hưởng của injury-based reporting; dùng `adjusted_ksi_collisions` khi so sánh giữa các năm.
- Cờ `collision_injury_based` không phản ánh đúng hệ thống ghi nhận của mọi lực lượng: Metropolitan Police có cờ 0 cho 2021–2024 và 1 cho 2025, nhưng số serious hiệu chỉnh bằng số gốc ở mọi năm (DfT đã coi là injury-based). Không dùng cờ này làm chỉ báo chất lượng; dùng số hiệu chỉnh.
- 64% bản ghi AADF là ước tính; LA traffic cũng là số ước tính của DfT.
