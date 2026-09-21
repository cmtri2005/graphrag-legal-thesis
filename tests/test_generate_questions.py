"""C2 — nothing a model writes is kept without passing this."""
from generate_questions import INSUFFICIENT, system_prompt, user_prompt, validate

TITLE = ("Thông tư số 36/2016/TT-BTTTT Quy định chi tiết về việc cấp phép hoạt động "
         "và chế độ báo cáo đối với loại hình báo nói, báo hình")
LEAD_IN = "Trong Thông tư này, các từ ngữ dưới đây được hiểu như sau:"
ANSWER = ("1. Giấy phép hoạt động phát thanh: là Giấy phép hoạt động báo chí được cấp cho "
          "tổ chức hoạt động báo nói. Giấy phép này quy định kênh phát thanh đầu tiên "
          "của tổ chức được cấp phép trong thời hạn 90 ngày.")
CONTEXT = f"{TITLE}\n{LEAD_IN}"


def _check(question):
    return validate(question, CONTEXT, ANSWER)


def test_a_well_formed_question_passes():
    assert _check("Theo quy định về cấp phép hoạt động đối với loại hình báo nói, "
                  "giấy phép hoạt động phát thanh được cấp cho đối tượng nào?") is None


def test_a_date_is_never_allowed_in_the_question():
    """The anchor is the `as_of` field; a date in the text would break C3."""
    assert _check("Theo quy định về cấp phép báo nói, năm 2017 giấy phép được cấp cho ai?") == "mentions_a_date"
    assert _check("Theo quy định về cấp phép, tính đến ngày 16/02/2017 ai được cấp phép?") == "mentions_a_date"


def test_the_question_asks_about_content_not_about_position():
    assert _check("Theo Thông tư này, Khoản 1 Điều 3 quy định nội dung gì?") == "cites_a_provision"
    assert _check("Theo quy định, Thông tư 36/2016/TT-BTTTT định nghĩa thế nào?") == "cites_a_provision"


def test_conversational_register_is_rejected():
    assert _check("Cho em hỏi giấy phép hoạt động phát thanh được cấp cho ai ạ?") == "conversational_filler"
    assert _check("Theo quy định về cấp phép, ai được cấp giấy phép phát thanh nhé?") == "conversational_filler"


def test_a_number_the_model_invented_is_rejected():
    assert _check("Theo quy định về cấp phép, giấy phép có thời hạn 45 ngày "
                  "áp dụng cho đối tượng nào?") == "unsourced_number:45"
    # 90 is in the answer, so it is sourced — C2 allows it.
    assert _check("Theo quy định về cấp phép báo nói, thời hạn 90 ngày "
                  "áp dụng cho loại giấy phép nào?") is None


def test_a_question_that_copies_the_answer_is_rejected():
    leaked = ("Theo quy định, có phải là Giấy phép hoạt động báo chí được cấp cho "
              "tổ chức hoạt động báo nói không?")
    assert _check(leaked) == "copies_the_answer"


def test_the_shape_of_the_output_is_enforced():
    assert _check("Theo quy định về cấp phép, giấy phép được cấp cho đối tượng nào.") == "not_a_question"
    assert _check("Câu 1?\nCâu 2?") == "not_one_line"
    assert _check("") == "not_one_line"
    assert _check(INSUFFICIENT) == "insufficient_context"
    assert _check("Ai vậy?") == "too_short"


def test_the_prompt_is_the_one_stored_in_the_repo():
    """C1: the prompt lives in the repo, not in the script."""
    system = system_prompt("T1")
    assert "KHONG_DU_NGU_CANH" in system
    assert "NHÓM T1" in system
    assert "cho em hỏi" in system.lower()      # the register rule is carried
    for group in ("T2", "T3", "T4", "T6"):
        assert f"NHÓM {group}" in system_prompt(group)


def test_one_question_serves_every_date_so_the_model_sees_every_version():
    """C3: a T2 pair shares one question, so both texts go in one prompt."""
    records = [{"as_of": "2015-01-01", "answer": "bản cũ", "target": {"document_title": TITLE, "lead_in": LEAD_IN}},
               {"as_of": "2020-01-01", "answer": "bản mới", "target": {"document_title": TITLE, "lead_in": LEAD_IN}}]
    message, context, answer = user_prompt(records)

    assert "CÁC PHIÊN BẢN" in message and "[1] bản cũ" in message and "[2] bản mới" in message
    assert LEAD_IN in context and "bản cũ" not in context   # framing is reusable, answers are not
    assert "bản cũ" in answer and "bản mới" in answer


def test_wording_the_document_title_already_uses_is_not_a_leak():
    """The anchoring rule tells the model to reuse the subject; C2 must not
    then punish it for doing so. Only a run it could only have got from the
    answer counts."""
    title = ("Nghị định số 68/2008/NĐ-CP Quy định điều kiện, thủ tục thành lập, tổ chức, "
             "hoạt động và giải thể cơ sở bảo trợ xã hội")
    lead_in = "3. Hồ sơ xin giải thể cơ sở bảo trợ xã hội gồm có:"
    answer = "a) Đơn xin giải thể cơ sở bảo trợ xã hội nêu rõ lý do xin giải thể;"
    context = f"{title}\n{lead_in}"

    assert validate("Theo quy định về thủ tục giải thể cơ sở bảo trợ xã hội, loại đơn trong "
                    "hồ sơ giải thể được gọi tên thế nào?", context, answer) is None
    # A run that exists only in the answer is still a leak.
    assert validate("Theo quy định, có phải đơn phải nêu rõ lý do xin giải thể cơ sở bảo trợ "
                    "xã hội nêu rõ lý do không?", context, answer) == "copies_the_answer"


def test_the_present_tense_that_real_vietnamese_legal_qa_uses_is_rejected():
    """Published Vietnamese legal QA opens with "Theo quy định pháp luật hiện
    hành" — which pins the question to the reader's present, and the anchor
    here is `as_of`."""
    for wrong in ("Theo quy định pháp luật hiện hành, hồ sơ gồm những giấy tờ nào?",
                  "Theo quy định hiện nay, thời hạn giải quyết là bao lâu?",
                  "Quy định đang có hiệu lực về hồ sơ giải thể yêu cầu những gì?"):
        assert validate(wrong, CONTEXT, ANSWER) == "presumes_the_present"


def test_the_examples_in_the_prompt_agree_with_the_validator():
    """Prompt and C2 must not drift: an example the validator rejects teaches
    the model to produce rejects, and a ✗ example it accepts teaches nothing."""
    air_context = ("Nghị định số 162/2018/NĐ-CP Quy định xử phạt vi phạm hành chính trong lĩnh vực "
                   "hàng không dân dụng\n2. Phạt tiền từ 20.000.000 đồng (hai mươi triệu đồng) đến "
                   "40.000.000 đồng (bốn mươi triệu đồng) đối với một trong các hành vi vi phạm sau đây:")
    air_answer = ("b) Đào tạo, bồi dưỡng, huấn luyện chuyên môn, nghiệp vụ cho nhân viên hàng không "
                  "không đúng nội dung; không đủ số giờ theo quy định;")

    # The ✓ example for a list item, quoted from prompts/vilextime/base.md.
    assert validate("Trong nhóm hành vi bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng về xử phạt "
                    "hành chính trong lĩnh vực hàng không dân dụng, hành vi đào tạo huấn luyện chuyên "
                    "môn nghiệp vụ sai quy định được mô tả như thế nào?", air_context, air_answer) is None
    # The ✗ examples, each for the reason the prompt gives.
    assert validate("Theo quy định pháp luật hiện hành, hồ sơ giải thể gồm những giấy tờ gì?",
                    air_context, air_answer) == "presumes_the_present"
    assert validate("Khoản 1 Điều 3 Thông tư 36/2016/TT-BTTTT quy định nội dung gì?",
                    air_context, air_answer) == "cites_a_provision"
    # And the one C2 cannot catch: well-formed, but its gold is the whole list.
    # The prompt teaches against it; only the hand-check can enforce it.
    assert validate("Những hành vi nào bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng?",
                    air_context, air_answer) is None
