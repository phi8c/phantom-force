import axios from "axios";

export function getChatErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
    if (error.response?.status === 403) return "Bạn không có quyền chat trong knowledge space này.";
    if (!error.response) return "Không thể kết nối API chat. Kiểm tra backend và thử lại.";
    const detail = error.response.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Không thể nhận câu trả lời. Bạn có thể thử gửi lại câu hỏi.";
}
