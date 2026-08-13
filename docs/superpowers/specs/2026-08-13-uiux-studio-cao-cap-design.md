# Thiết Kế UI/UX Studio Cao Cấp

Ngày: 2026-08-13
Phạm vi: Cập nhật giao diện web hiện có của AI Media Agent Studio theo hướng studio sáng tạo cao cấp, nền tối, tương phản mạnh, preview nổi bật.

## Mục Tiêu

Giao diện hiện tại dùng tốt nhưng còn giống form dashboard sáng màu. Bản cập nhật cần tạo cảm giác một công cụ studio chuyên nghiệp cho tạo ảnh/video, trong đó vùng preview là trung tâm thị giác, composer vẫn nhanh và rõ, trạng thái job dễ đọc, và lịch sử tác vụ hỗ trợ quay lại kết quả gần đây.

Không biến màn hình đầu thành landing page. Người dùng vào app phải thấy ngay công cụ tạo nội dung.

## Hướng Thiết Kế

Chọn hướng Cinematic Control Room:

- Nền tối sâu, surface phân lớp, tương phản rõ giữa composer và preview.
- Accent dùng tiết chế: teal cho trạng thái hoạt động/thành công, amber cho render/queue, red cho lỗi.
- Typography chắc, gọn, không dùng hero quá lớn trong panel thao tác.
- Preview panel thành stage chính với khung xem rộng, empty/loading state có cảm giác render chuyên nghiệp.
- Composer giống bàn điều khiển: prompt chính nổi bật, controls phụ gọn, preset thành shot cards.

## Cấu Trúc Giao Diện

Header:

- Giữ brand `AI Media Agent`, đổi cảm giác sang studio bar tối.
- Health status hiển thị như signal pill, dễ nhận biết provider/prompt provider.
- Navigation giữ đơn giản, không chiếm sự chú ý khỏi workspace.

Topbar:

- Chuyển thành command strip: eyebrow, tiêu đề ngắn, mô tả phụ nhỏ, status/provider capsule.
- Không dùng section hero marketing.

Composer:

- Panel tối, viền tinh tế, có shadow nhẹ.
- Prompt textarea là control chính, chiếm trọng lượng nhiều nhất trong form.
- Image/video tabs rõ trạng thái active.
- Preset buttons đổi thành cards nhỏ có nhãn hành động, hover/focus nổi hơn.
- Primary action nổi bật hơn secondary action.

Preview:

- Preview hero và result frame hợp nhất về cảm giác stage.
- Empty state có tiêu đề và mô tả ngắn, không quá minh họa.
- Khi job queued/running, hiển thị trạng thái nổi hơn bằng badge màu amber và vùng chờ có cảm giác render.
- Khi completed, ảnh/video dùng tối đa không gian hợp lý, không bị khung sáng làm mất chất cinematic.
- JSON dry-run vẫn đọc được trên nền tối.

Recent Jobs:

- Chuyển thành timeline/list compact dưới workspace.
- Mỗi item có loại media, prompt, thời gian, hover rõ.
- Không thêm workflow mới ngoài chọn lại job hiện có.

## Hành Vi Và Trạng Thái

- Giữ nguyên API base URL và logic gọi API hiện tại.
- Giữ `localStorage` recent jobs hiện có.
- Có thể bổ sung class trạng thái body/result nếu cần, nhưng không thay đổi contract API.
- Loading/busy state phải disable nút như hiện tại và đổi copy phù hợp.
- Mobile: layout một cột, preview không bị chèn dưới form quá chật, text không tràn khỏi button/card.

## Files Dự Kiến Sửa

- `web/index.html`: thêm copy/structure nhỏ cho command strip, preset cards, preview stage nếu cần.
- `web/static/css/styles.css`: thay visual system sang dark cinematic, responsive states, hover/focus/loading polish.
- `web/static/js/app.js`: chỉ sửa nếu cần cập nhật labels/empty state markup hoặc thêm class trạng thái; tránh đổi logic API.
- `tests/test_api.py`: thêm hoặc cập nhật assertions để bảo vệ các anchor UI quan trọng nếu markup mới thay đổi.

## Kiểm Thử

- TDD cho thay đổi behavior/markup có thể test bằng `TestClient` trên `/` và static assets.
- Chạy `pytest` sau khi sửa.
- Nếu khởi động được server, kiểm tra thủ công `http://127.0.0.1:8001/` trên desktop và mobile width trong browser nếu tool/browser sẵn sàng.

## Ngoài Phạm Vi

- Không thêm provider mới.
- Không thay đổi API backend.
- Không thêm framework frontend hoặc build step.
- Không tạo landing page riêng.
- Không thay đổi ảnh asset trừ khi cần thiết cho layout.