import re

reg_texts = """
%REALADDR 0x80064400
%BASE 0x4400
%SIZE 0xc00

%A 0x0 "Function Reset register"
31    flush_done      re  0x0  "read clear,flush done"
30:16 reset_qid       re  0x0  "reset queue id"
7:0   reset_fid       ro  0x0  "reset function id"

%A 0x1 "Retransmit control register"
31    fde_flh_done    ro  0x0  "flush done, then can enable this function"
16    fde_flh_en      re  0x0  "write this bit 1,then flush the function indicated by fde_fid"
15    fde_en          re  0x0  "if read return 1,then it can disable or enable some function,if write this bit 1,if will triger enable/dis operation"
14    fde_up_down     rw  0x0  "function enable/disable bit"
13    fde_drop        rw  0x0  "function enable/disable bit"
7:0   fde_fid         rw  0x0  "function id enable/disable or flush"

%A 0x2 " msix trigger register"
31       cfg_msix_tri        re  0x0  "cfg int triger,read 0: available; read 1: not available" 
23:16    cfg_msix_fid        rw  0x0  "function id that configuration change" 
15:0     cfg_msix_vector     rw  0x0  "configuration change msix vector"

%A 0x4 "svn version register"
31:0  svn_version     ro  0x0  "svn version register"

%A 0x8 "erom  register"
31:0  erom_base     rw  0x0  "expand rom base addr "

%A 0x9 "erom  register"
0  erom_init     rw  0x0  "expand rom intial  "

%A 0x100 "outstanding cmd num limit"
15:0 out_cmd_max rw 0x80 "outstanding cmd mun max"
%A 0x101 "outstanding cmd mun"
15:0 out_cmd_num ro 0x80 "outstanding cmd mun "

%A 0x102 "blk debug0 "
31:0 debug0 ro 0x0 " debug "

%A 0x103 "blk debug1 "
31:0 debug1 ro 0x0 " debug "

%A 0x104 "blk debug2 "
31:0 debug2 ro 0x0 " debug "

%A 0x105 "blk debug3 "
31:0 debug3 ro 0x0 " debug "

%A 0x106 "blk debug4 "
31:0 debug4 ro 0x0 " debug "

%A 0x107 "blk debug5 "
31:0 debug5 ro 0x0 " debug "

%A 0x108 "blk debug6 "
31:0 debug6 ro 0x0 " debug "

%A 0x109 "blk debug7 "
31:0 debug7 ro 0x0 " debug "

%A 0x10a "blk debug8 "
31:0 debug8 ro 0x0 " debug "

%A 0x10b "blk debug9 "
31:0 debug9 ro 0x0 " debug "

%A 0x10c "blk debug10 "
31:0 debug10 ro 0x0 " debug "

%A 0x10d "blk debug11 "
31:0 debug11 ro 0x0 " debug "

%A 0x10e "blk debug12 "
31:0 debug12 ro 0x0 " debug "

%A 0x10f "blk debug13 "
31:0 debug13 ro 0x0 " debug "

%A 0x110 "blk debug14 "
31:0 debug14 ro 0x0 " debug "

%A 0x111 "blk debug15 "
31:0 debug15 ro 0x0 " debug "

%A 0x112 "blk debug16 "
31:0 debug16 ro 0x0 " debug "






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

%A 0x2fe "live migration register"
31:0  queue_idx      re  0x0  "31:16 avail_idx;15:0 used_idx; head:host write,FW read;FW write,host read"

%A 0x2ff "live migration register"
31:0   debug          re  0x0  "fw read/write and host read/write register"
"""

reg_blocks = re.split(r'\n(?=%A)', reg_texts)
for reg_blk in reg_blocks:
    # print(reg_blk)
    print('=' * 50)
    bit_blocks = re.split(r'\n(?=\d)', reg_blk)
    for bit_blk in bit_blocks:
        print(bit_blk)
        print('-' * 50)


