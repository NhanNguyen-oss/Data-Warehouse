"""
CO4031 | Khung thành phần hệ hỗ trợ quyết định (DSS).

Mô hình bám ba giai đoạn ra quyết định của Simon:
    Intelligence  — nhận diện tình huống từ số liệu kho dữ liệu
    Design        — chấm điểm các phương án theo tiêu chí có trọng số
    Choice        — chọn phương án và giải thích vì sao

Chạy thử:
    python src/dss/model.py

Việc nhóm phải thay:
    - Nguồn đầu vào: aggregate từ dw.* (không quyết định trên dữ liệu tác nghiệp thô).
    - Bộ tiêu chí, trọng số và ngưỡng: gắn với bài toán đã chốt ở giai đoạn 1.
    - Phần đánh giá: so sánh quyết định gợi ý với một mốc thực tế hoặc kịch bản what-if.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Criterion:
    """Một tiêu chí. higher_is_better=False khi giá trị càng thấp càng tốt (rủi ro, chi phí)."""

    name: str
    weight: float
    higher_is_better: bool = True


@dataclass(frozen=True)
class Alternative:
    """Một phương án. scores: tên tiêu chí -> giá trị thô đo được từ kho dữ liệu."""

    name: str
    scores: dict[str, float]


@dataclass(frozen=True)
class Recommendation:
    chosen: str
    ranking: list[tuple[str, float]]
    reason: str


class DecisionSupportModel:
    """Chấm điểm có trọng số, chuẩn hóa min-max trên tập phương án đang xét."""

    def __init__(self, criteria: list[Criterion], choice_threshold: float = 0.0) -> None:
        total = sum(item.weight for item in criteria)
        if total <= 0:
            raise ValueError("Tổng trọng số phải lớn hơn 0.")
        self.criteria = criteria
        self.choice_threshold = choice_threshold
        self._weight_sum = total

    def intelligence(self, alternatives: list[Alternative]) -> list[Alternative]:
        """Lọc phương án không đủ dữ liệu tiêu chí. Đây là bước nhận diện tình huống."""
        required = {item.name for item in self.criteria}
        ready = [item for item in alternatives if required.issubset(item.scores)]
        if not ready:
            raise ValueError("Không có phương án nào đủ tiêu chí để xét.")
        return ready

    def design(self, alternatives: list[Alternative]) -> list[tuple[str, float]]:
        """Chuẩn hóa từng tiêu chí về [0, 1] rồi tính điểm có trọng số."""
        ranking: list[tuple[str, float]] = []
        for alternative in alternatives:
            score = 0.0
            for criterion in self.criteria:
                values = [item.scores[criterion.name] for item in alternatives]
                low, high = min(values), max(values)
                raw = alternative.scores[criterion.name]
                if high == low:
                    normalized = 1.0
                else:
                    normalized = (raw - low) / (high - low)
                if not criterion.higher_is_better:
                    normalized = 1.0 - normalized
                score += normalized * (criterion.weight / self._weight_sum)
            ranking.append((alternative.name, round(score, 4)))
        ranking.sort(key=lambda item: item[1], reverse=True)
        return ranking

    def choice(self, ranking: list[tuple[str, float]]) -> Recommendation:
        """Chọn phương án điểm cao nhất nếu vượt ngưỡng; nếu không, đề nghị chưa quyết."""
        best_name, best_score = ranking[0]
        if best_score < self.choice_threshold:
            return Recommendation(
                chosen="CHUA_QUYET",
                ranking=ranking,
                reason=(
                    f"Điểm cao nhất ({best_score}) thấp hơn ngưỡng {self.choice_threshold}. "
                    "Cần thêm dữ liệu hoặc nới tiêu chí."
                ),
            )
        return Recommendation(
            chosen=best_name,
            ranking=ranking,
            reason=f"Chọn {best_name} vì điểm tổng hợp {best_score} là cao nhất.",
        )

    def recommend(self, alternatives: list[Alternative]) -> Recommendation:
        ready = self.intelligence(alternatives)
        ranking = self.design(ready)
        return self.choice(ranking)


def _demo() -> Recommendation:
    """
    Bài toán mẫu: chọn nhóm hàng cần tăng nhập.

    TODO: thay DEMAND / MARGIN / RISK bằng số đo thật từ kho dữ liệu,
    ví dụ nhu cầu 4 tuần, biên lợi nhuận, tỷ lệ trả hàng.
    """
    model = DecisionSupportModel(
        criteria=[
            Criterion("demand", weight=0.5, higher_is_better=True),
            Criterion("margin", weight=0.3, higher_is_better=True),
            Criterion("risk", weight=0.2, higher_is_better=False),
        ],
        choice_threshold=0.45,
    )
    alternatives = [
        Alternative("Nhom A", {"demand": 180, "margin": 0.22, "risk": 0.10}),
        Alternative("Nhom B", {"demand": 140, "margin": 0.35, "risk": 0.40}),
        Alternative("Nhom C", {"demand": 90, "margin": 0.18, "risk": 0.05}),
    ]
    return model.recommend(alternatives)


if __name__ == "__main__":
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    result = _demo()
    print("Phuong an:", result.chosen)
    print("Xep hang:", result.ranking)
    print("Ly do:", result.reason)
