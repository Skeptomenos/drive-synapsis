
from html.parser import HTMLParser
import re

class GoogleDocHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.current_line = []
        self.indent_level = 0
        self.in_list_item = False
        self.list_type = [] # 'ul' or 'ol'
        self.is_bold = False
        self.is_italic = False
        self.link_url = None
        self.image_alt = None
        
        # Table State
        self.in_table = False
        self.table_rows = []
        self.current_table_row = []
        self.in_cell = False
        
        # Buffer to help detect adjacency
        self.last_tag_end_pos = 0 # Not easy to track absolute pos, but we can track if we just ended a tag
        self.just_closed_inline_tag = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        # self.just_closed_inline_tag = False # Don't clear here! We need to know if we just ended one.
        
        if tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            self._flush_line()
            
        if tag == 'h1': self.current_line.append('# ')
        elif tag == 'h2': self.current_line.append('## ')
        elif tag == 'h3': self.current_line.append('### ')
        elif tag == 'h4': self.current_line.append('#### ')
        
        elif tag == 'ul':
            self.list_type.append('ul')
            self.indent_level += 1
        elif tag == 'ol':
            self.list_type.append('ol')
            self.indent_level += 1
        elif tag == 'li':
            indent = "  " * (self.indent_level - 1)
            marker = "* " if self.list_type[-1] == 'ul' else "1. "
            self.current_line.append(f"{indent}{marker}")
            
        elif tag == 'b' or tag == 'strong':
            self.is_bold = True
            self.current_line.append('**')
        elif tag == 'i' or tag == 'em':
            self.is_italic = True
            self.current_line.append('*')
            
        elif tag == 'a':
            self.link_url = attrs_dict.get('href')
            self.current_line.append('[')
            
        elif tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', 'Image')
            self.current_line.append(f"![{alt}]({src})")

            
        elif tag == 'table':
            self._flush_line()
            self.in_table = True
            self.table_rows = []
        elif tag == 'tr':
            self.current_table_row = []
        elif tag == 'td' or tag == 'th':
            self.in_cell = True
            # Flush output to a temp buffer or just mark index?
            # We need to capture cell content cleanly.
            # Simplified: Flush current line, capture everything until /td into a specific buffer?
            # Existing architecture appends to self.current_line.
            # We can let it append, and on /td we consume self.current_line?
            self._flush_line() # Clear garbage
            
        elif tag == 'span':
            # Check for styles that indicate boldness/italics (Google Docs specific)
            style = attrs_dict.get('style', '').lower()
            if 'font-weight:700' in style or 'font-weight:bold' in style:
                self.current_line.append('**')
                self.is_bold = True
            if 'font-style:italic' in style:
                self.current_line.append('*')
                self.is_italic = True

    def handle_endtag(self, tag):
        if tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            self._flush_line()
            self.current_line.append('\n')
            if tag in ['p']: self.current_line.append('\n') # Double newline for paragraphs
            
        elif tag in ['ul', 'ol']:
            self.list_type.pop()
            self.indent_level -= 1
            
        elif tag == 'b' or tag == 'strong':
            self.current_line.append('**')
            self.is_bold = False
            self.just_closed_inline_tag = True
            
        elif tag == 'i' or tag == 'em':
            self.current_line.append('*')
            self.is_italic = False
            self.just_closed_inline_tag = True
            
        elif tag == 'a':
            # Close markdown link: [text](url)
            if self.link_url:
                self.current_line.append(f']({self.link_url})')
                self.link_url = None
            else:
                self.current_line.append(']')  # No URL, just close bracket
            self.just_closed_inline_tag = True
            
        elif tag == 'table':
            self.in_table = False
            self._flush_line()
            # Render Table
            if self.table_rows:
                # 1. Header
                header = self.table_rows[0]
                cols = len(header)
                self.output.append("| " + " | ".join(header) + " |")
                self.output.append("| " + " | ".join(['---'] * cols) + " |")
                # 2. Body
                for row in self.table_rows[1:]:
                    # Pad row if short
                    while len(row) < cols: row.append('')
                    self.output.append("| " + " | ".join(row[:cols]) + " |")
                self.output.append("") # Newline after table

        elif tag == 'tr':
            self.table_rows.append(self.current_table_row)
            
        elif tag == 'td' or tag == 'th':
            # Consume content from current_line as cell data
            cell_content = "".join(self.current_line).strip()
            self.current_line = []
            self.current_table_row.append(cell_content)
            self.in_cell = False
            
        elif tag == 'span':
            if self.is_italic: self.current_line.append('*')
            if self.is_bold: self.current_line.append('**')
            self.is_bold = False
            self.is_italic = False
            self.just_closed_inline_tag = True

    def handle_data(self, data):
        # Normalize whitespace (but keep meaningful spaces?)
        # For Google Docs HTML, newlines in data are usually meaningless
        text = data.replace('\n', ' ')
        
        if not text:
            return

        # CRITICAL FIX: Adjacent Spans Concatenation
        # If we just closed an inline tag (like </span>) and now we have non-whitespace text,
        # implies we are starting a new text block immediately after the previous one.
        # If the text itself doesn't start with space, we should add one.
        if self.just_closed_inline_tag and text and not text[0].isspace():
             self.current_line.append(' ')
             
        self.current_line.append(text)
        self.just_closed_inline_tag = False

    def _flush_line(self):
        if self.current_line:
            # Join and clean up multiple spaces
            raw_line = "".join(self.current_line)
            # Simple cleanup but careful not to kill markdown syntax
            self.output.append(raw_line)
            self.current_line = []

    def get_markdown(self):
        self._flush_line()
        return "".join(self.output).strip()

def convert_html_to_markdown(html_content: str) -> str:
    parser = GoogleDocHtmlParser()
    parser.feed(html_content)
    return parser.get_markdown()
