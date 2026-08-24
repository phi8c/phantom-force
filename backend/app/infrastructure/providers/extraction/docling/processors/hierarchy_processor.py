import re
from app.infrastructure.providers.extraction.docling.models.section import SectionModel, TableModel, ImageModel
from app.infrastructure.providers.extraction.docling.processors.text_processor import clean_text

class HierarchyProcessor:
    def _detect_level_by_title(self, title: str, docling_level: int) -> int:
        """
        Bổ sung Heuristic để sửa lỗi Docling nhận diện sai level (Lỗi chí mạng ở trên)
        """
        # Nếu bắt đầu bằng "Chương" hoặc viết hoa toàn bộ tiêu đề lớn -> Level 1
        if re.match(r"^(Chương\s+\d\s+H+|KẾOẠCH)", title, re.IGNORECASE):
            return 1
        # Nếu có dạng "1.1", "2.3.1" -> Tính dựa trên số dấu chấm
        match = re.match(r"^(\d+(\.\d+)+)", title)
        if match:
            return match.group(1).count('.') + 1
        
        return docling_level if docling_level > 0 else 1

    def process(self, docling_doc) -> list[SectionModel]:
        root_sections = []
        stack = []  # Lưu (level, SectionModel)
        
        # Ghost Root tạm thời
        ghost_root = SectionModel(id="ghost-root", title="Root", level=0, page_no=1)
        stack.append((0, ghost_root))
        
        for item, _ in docling_doc.iterate_items():
            page_no = item.prov[0].page_no if getattr(item, 'prov', None) else None
            label = getattr(item, 'label', '')
            
            # 1. XỬ LÝ HEADING
            if label == 'section_header':
                raw_title = clean_text(item.text)
                docling_level = getattr(item, 'level', 1)
                
                # Ép lại level chuẩn dựa trên text tiêu đề
                actual_level = self._detect_level_by_title(raw_title, docling_level)
                
                new_section = SectionModel(
                    id=getattr(item, 'self_ref', f"sec-{item.text[:10]}"),
                    title=raw_title,
                    level=actual_level,
                    page_no=page_no
                )
                
                # Tìm cha phù hợp trong Stack
                while stack and stack[-1][0] >= actual_level:
                    stack.pop()
                
                # Gắn vào cha gần nhất
                if stack:
                    stack[-1][1].children.append(new_section)
                
                stack.append((actual_level, new_section))
                
            # 2. XỬ LÝ TEXT / PARAGRAPH
            elif label in ['text', 'paragraph', 'list_item']:
                text_val = clean_text(item.text)
                # Chỉ push text vào Node lá hiện tại (Node đang ở đỉnh stack)
                if stack and stack[-1][1].id != "ghost-root":
                    current_node = stack[-1][1]
                    if current_node.content:
                        current_node.content += "\n" + text_val
                    else:
                        current_node.content = text_val
                        
            # 3. XỬ LÝ TABLE
            elif label == 'table':
                if stack and stack[-1][1].id != "ghost-root":
                    stack[-1][1].tables.append(TableModel(
                        content=item.export_to_markdown(),
                        page_no=page_no
                    ))
                    
            # 4. XỬ LÝ PICTURE
            elif label == 'picture':
                if stack and stack[-1][1].id != "ghost-root":
                    caption_text = clean_text(item.text) if hasattr(item, 'text') else None
                    stack[-1][1].images.append(ImageModel(
                        caption=caption_text,
                        page_no=page_no
                    ))
                    
        for section in ghost_root.children:

            self._calculate_metrics(
                section,
            )
                    
        return ghost_root.children  # Trả về các nút con của ghost root để loại bỏ node rỗng bọc ngoài
    
    
    def _calculate_metrics(
        self,
        section: SectionModel,
    ) -> tuple[str, int]:

        aggregated_content = (
            section.content
        )

        token_count = (
            self._estimate_tokens(
                section.content,
            )
        )

        aggregated_token_count = (
            token_count
        )

        for child in section.children:

            (
                child_content,
                child_token_count,
            ) = self._calculate_metrics(
                child,
            )

            if child_content:

                if aggregated_content:

                    aggregated_content += (
                        "\n\n"
                        + child_content
                    )

                else:

                    aggregated_content = (
                        child_content
                    )

            aggregated_token_count += (
                child_token_count
            )

        section.token_count = (
            token_count
        )

        section.aggregated_content = (
            aggregated_content
        )

        section.aggregated_token_count = (
            aggregated_token_count
        )

        return (
            aggregated_content,
            aggregated_token_count,
        )
        
    def _estimate_tokens(
        self,
        text: str,
    ) -> int:

        if not text:
            return 0

        return len(
            text.split()
        )