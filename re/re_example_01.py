import re

texts = """
%A 0x2fd "live migration register"
31:28   status        re  0x0  "0h:idle;
				1h: reset pending;
				2h:rd_idx_pending;
				3h:wr_idx pending;
				4h:resume_pending;
				5h:reset_done;
				6h:rd_idx_done;
				7h:wr_idx_done;
				8h:resume done;
				9h:disable done"
27:24   opcode        ro  0x0  "0h:none; 
				1h: reset; 
				2h:rd_idx;
				3h:wr_idx;
				4h:resume;
				5h:disable "
23:16   op_qid        ro  0x0  "indicates the logic qid host operate  "
15:0    op_value      ro  0x0  "if reset/resume, this value is function id,otherwise this value is queue id"
"""
header_match = re.search(r'%A\s+(0x[0-9a-fA-F]+)\s+"([^"]+)"', texts)
# print(header_match)
# print(header_match.group(1))
# print(header_match.group(2))
fd_line = """
31:28   status        re  0x0  "0h:idle;
				1h: reset pending;
				2h:rd_idx_pending;
				3h:wr_idx pending;
				4h:resume_pending;
				5h:reset_done;
				6h:rd_idx_done;
				7h:wr_idx_done;
				8h:resume done;
				9h:disable done"
"""
field_match = re.match(r'([\d:]+)\s+(\w+)\s+(\w+)\s+(\S+)\s+"([^"]+)"', fd_line.strip())
print(f'field_match --> {field_match}')
print(f'field_match.group(1) --> {field_match.group(1)}')
print(f'field_match.group(2) --> {field_match.group(2)}')
print(f'field_match.group(3) --> {field_match.group(3)}')
print(f'field_match.group(4) --> {field_match.group(4)}')
print(f'field_match.group(5) --> {field_match.group(5)}')
