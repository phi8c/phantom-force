Hướng kiến trúc sẽ làm

Pipeline ingest sẽ được chia thành Business Event và Execution Queue.

Business Event sẽ là nguồn sự thật (Source of Truth) của luồng nghiệp vụ. Mỗi khi một stage hoàn thành, Worker không tự dispatch sang các stage tiếp theo, mà chỉ phát sinh một Event. Ví dụ ExtractWorker sau khi tạo ra DocumentExtraction sẽ chỉ publish DocumentExtractedEvent.

Event Bus sẽ chịu trách nhiệm fan-out sự kiện này tới tất cả các Handler đã đăng ký. Mỗi Handler đại diện cho một nhánh nghiệp vụ độc lập. Ví dụ SaveExtractionHandler, SaveStorageHandler, ChunkHandler đều cùng lắng nghe DocumentExtractedEvent.

Các Handler không xử lý nghiệp vụ nặng. Chúng chỉ chuyển Event thành công việc thực thi bằng cách enqueue vào Queue tương ứng.

Ví dụ:

SaveExtractionHandler → SaveExtractionQueue
SaveStorageHandler → SaveStorageQueue
ChunkHandler → ChunkQueue

Sau đó các Worker của từng Queue sẽ chạy song song, độc lập với nhau:

SaveExtractionWorker lưu Database.
SaveStorageWorker upload Supabase Storage.
ChunkWorker thực hiện chunking.

Điều quan trọng là Event định nghĩa Business Flow, còn Queue chỉ là Execution Topology. Sau này muốn thêm OCR, Graph, Audit, Notification, Entity Extraction... chỉ cần đăng ký thêm Handler mới cho DocumentExtractedEvent mà không phải sửa ExtractWorker. Đây đúng với mục tiêu mở rộng lâu dài của hệ thống và tận dụng được Event Bus đã xây dựng.