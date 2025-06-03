# 分析下面的代码，指出存在的问题，并修改正确
import re

reg_block_list = [
'%REALADDR 0x205202A000\n%BASE 0x0000\n%SIZE 0x1000\n\n', 
 '%A  0x00    "RXP_PKP rqf_conf0 register"\n31:0    pkp_rqf_conf0       rw  0x84000000  "bit[0]: prefetch_en; bit[1]: low priority prefetch en; bit[2]: carry_prefetch_en; bit[27:24]: dft_prefetch_cnt; bit[31:28]: max_prefetch_cnt;"\n\n', 
 '%A  0x01    "RXP_PKP rqf_conf1 register"\n31:0    pkp_rqf_conf1       rw  0x10001     "bit[7:0]: max_aggr_num; [31:16]: aggr_timeout_thd."\n\n', 
 '%A  0x02    "RXP_PKP rqf_conf2 register"\n31:0    pkp_rqf_conf2       rw  0x2000008         "bit[15:0]: rqf_dalc_lqp lkup inf period; [31:16]: prefetch rwqe limit number"\n\n', 
 '%A  0x03    "RXP_PKP lchsch ack type packet port fc function enable register"\n0:0     pkp_lchsch_ack_port_fc_en   rw          "RXP_PKP lchsch ack type packet port fc function enable register"\n\n', '%A  0x04    "RXP_PKP lchsch rdresp type packet port fc function enable register"\n0:0     pkp_lchsch_rdresp_port_fc_en   rw          "RXP_PKP lchsch rdresp type packet port fc function enable register"\n\n', 
 '%A  0x08    "RXP_PKP rdlog_base_ram_waddr register"\n7:0     rdlog_base_ram_waddr    rw          "Indirect access to rdlog_base_ram, write the waddr to this register"\n\n', 
 '%A  0x09    "RXP_PKP rdlog_base_ram_wdata0 register"\n31:0    rdlog_base_ram_wdata0   rw          "Indirect access to rdlog_base_ram, write the wdata[31:0] to this register"\n\n', 
 '%A  0x0A    "RXP_PKP rdlog_base_ram_wdata1 register"\n31:0    rdlog_base_ram_wdata1   re          "Indirect access to rdlog_base_ram, write the wdata[63:32] to this register. In a round of writing access to rdlog_base_ram, this register must be the last DW being written."\n\n', 
 '%A  0x0C    "RXP_PKP rdlog_base_ram_raddr register"\n7:0     rdlog_base_ram_raddr    re          "Indirect access to rdlog_base_ram, write the raddr to this register. In a round of reading access to rdlog_base_ram, write this register firstly, then get rdlog_base_ram_rdata"\n\n', 
 '%A  0x0D    "RXP_PKP rdlog_base_ram_rdata0 register"\n31:0    rdlog_base_ram_rdata0   ro          "Indirect access to rdlog_base_ram, read this register to get rdlog_base_ram_rdata[31:0]"\n\n', 
 '%A  0x0E    "RXP_PKP rdlog_base_ram_rdata1 register"\n31:0    rdlog_base_ram_rdata1   ro          "Indirect access to rdlog_base_ram, read this register to get rdlog_base_ram_rdata[63:32]"\n\n', 
 '%A  0x10    "RXP_PKP rnr_nack_gen_log register"\n31:0    rnr_nack_gen_log    re          "When any RNR NACK is generated, its info will be logged here. Writing any value can clear this register. The definition is as following: bit[31]: log is valid; bit[30]: more than one RNR NACK is generated, but only logged the first one; bit[23:16]: internal process tag; bit[15:0]: QPID."\n\n', 
 '%A  0x20    "RXP_PKP  pkp_rqf_indir_dbg_cmd register"\n31:0     pkp_rqf_indir_dbg_cmd   re          "Debug only"\n\n', 
 '%A  0x21    "RXP PKP  pkp_rqf_indir_dbg_sta register"\n1:0      pkp_rqf_indir_dbg_sta   ro          "Debug only"\n\n', 
 '%A  0x24    "RXP_PKP  pkp_rqf_indir_dbg_data0 register"\n31:0     pkp_rqf_indir_dbg_data0 ro          "Debug only"\n\n', 
 '%A  0x25    "RXP_PKP  pkp_rqf_indir_dbg_data1 register"\n31:0     pkp_rqf_indir_dbg_data1 ro          "Debug only"\n\n', 
 '%A  0x26    "RXP_PKP  pkp_rqf_indir_dbg_data2 register"\n31:0     pkp_rqf_indir_dbg_data2 ro          "Debug only"\n\n', 
 '%A  0x27    "RXP_PKP  pkp_rqf_indir_dbg_data3 register"\n31:0     pkp_rqf_indir_dbg_data3 ro          "Debug only"\n\n', 
 '%A  0x44    "RXP_PKP ppl_dbg_reg0   register"\n31:0    ppl_dbg_reg0        ro          "Debug only"\n\n', 
 '%A  0x45    "RXP_PKP ppl_dbg_reg1   register"\n31:0    ppl_dbg_reg1        ro          "Debug only"\n\n', 
 '%A  0x46    "RXP_PKP ppl_dbg_reg2   register"\n31:0    ppl_dbg_reg2        ro          "Debug only"\n\n', 
 '%A  0x47    "RXP_PKP ppl_dbg_reg3   register"\n31:0    ppl_dbg_reg3        ro          "Debug only"\n\n', 
 '%A  0x48    "RXP_PKP ppl_dbg_reg4   register"\n31:0    ppl_dbg_reg4        ro          "Debug only"\n\n', 
 '%A  0x49    "RXP_PKP ppl_dbg_reg5   register"\n31:0    ppl_dbg_reg5        ro          "Debug only"\n\n', 
 '%A  0x4A    "RXP_PKP ppl_dbg_reg6   register"\n31:0    ppl_dbg_reg6        ro          "Debug only"\n\n', 
 '%A  0x4B    "RXP_PKP ppl_dbg_reg7   register"\n31:0    ppl_dbg_reg7        ro          "Debug only"\n\n', 
 '%A  0x50    "RXP PKP extr_dbg_reg0 register"\n31:0    extr_dbg_reg0     ro          "extr_dbg_reg0"\n\n', 
 '%A  0x51    "RXP PKP extr_dbg_reg1 register"\n31:0    extr_dbg_reg1     ro          "extr_dbg_reg1"\n\n', 
 '%A  0x52    "RXP PKP extr_dbg_reg2 register"\n31:0    extr_dbg_reg2     ro          "extr_dbg_reg2"\n\n', 
 '%A  0x53    "RXP PKP extr_dbg_reg3 register"\n31:0    extr_dbg_reg3     ro          "extr_dbg_reg3"\n\n', 
 '%A  0x54    "RXP PKP extr_dbg_reg4 register"\n31:0    extr_dbg_reg4     ro          "extr_dbg_reg4"\n\n', 
 '%A  0x55    "RXP PKP extr_dbg_reg5 register"\n31:0    extr_dbg_reg5     ro          "extr_dbg_reg5"\n\n', 
 '%A  0x56    "RXP PKP extr_dbg_reg6 register"\n31:0    extr_dbg_reg6     ro          "extr_dbg_reg6"\n\n', 
 '%A  0x57    "RXP PKP extr_dbg_reg7 register"\n31:0    extr_dbg_reg7     ro          "extr_dbg_reg7"\n\n', 
 '%A  0x58    "RXP PKP extr_dbg_reg8 register"\n31:0    extr_dbg_reg8     ro          "extr_dbg_reg8"\n\n', 
 '%A  0x60    "RXP_PKP wrdesc_dbg_reg0    register"\n31:0    wrdesc_dbg_reg0     ro          "Debug only"\n\n', 
 '%A  0x61    "RXP_PKP wrdesc_dbg_reg1    register"\n31:0    wrdesc_dbg_reg1     ro          "Debug only"\n\n', 
 '%A  0x62    "RXP_PKP wrdesc_dbg_reg2    register"\n31:0    wrdesc_dbg_reg2     ro          "Debug only"\n\n', 
 '%A  0x63    "RXP_PKP wrdesc_dbg_reg3    register"\n31:0    wrdesc_dbg_reg3     ro          "Debug only"\n\n', 
 '%A  0x64    "RXP_PKP wrdesc_dbg_reg4    register"\n31:0    wrdesc_dbg_reg4     ro          "Debug only"\n\n', 
 '%A  0x65    "RXP_PKP wrdesc_dbg_reg5    register"\n31:0    wrdesc_dbg_reg5     ro          "Debug only"\n\n', 
 '%A  0x66    "RXP_PKP wrdesc_dbg_reg6    register"\n31:0    wrdesc_dbg_reg6     ro          "Debug only"\n\n', 
 '%A  0x67    "RXP_PKP wrdesc_dbg_reg7    register"\n31:0    wrdesc_dbg_reg7     ro          "Debug only"\n\n', 
 '%A  0x68    "RXP_PKP wrdesc_dbg_reg8    register"\n31:0    wrdesc_dbg_reg8     ro          "Debug only"\n\n', 
 '%A  0x70    "RXP_PKP lchsch_dbg_reg0    register"\n31:0    lchsch_dbg_reg0     ro          "Debug only"\n\n', 
 '%A  0x71    "RXP_PKP lchsch_dbg_reg1    register"\n31:0    lchsch_dbg_reg1     ro          "Debug only"\n\n', 
 '%A  0x72    "RXP_PKP lchsch_dbg_reg2    register"\n31:0    lchsch_dbg_reg2     ro          "Debug only"\n\n', 
 '%A  0x73    "RXP_PKP lchsch_dbg_reg3    register"\n31:0    lchsch_dbg_reg3     ro          "Debug only"\n\n', 
 '%A  0x74    "RXP_PKP lchsch_dbg_reg4    register"\n31:0    lchsch_dbg_reg4     ro          "Debug only"\n\n', 
 '%A  0x75    "RXP_PKP lchsch_dbg_reg5    register"\n31:0    lchsch_dbg_reg5     ro          "Debug only"\n\n', 
 '%A  0x76    "RXP_PKP lchsch_dbg_reg6    register"\n31:0    lchsch_dbg_reg6     ro          "Debug only"\n\n', 
 '%A  0x77    "RXP_PKP lchsch_dbg_reg7    register"\n31:0    lchsch_dbg_reg7     ro          "Debug only"\n\n', 
 '%A  0x78    "RXP_PKP lchsch_dbg_reg8    register"\n31:0    lchsch_dbg_reg8     ro          "Debug only"\n\n', 
 '%A  0x79    "RXP_PKP lchsch_dbg_reg9    register"\n31:0    lchsch_dbg_reg9     ro          "Debug only"\n\n', 
 '%A  0x7a    "RXP_PKP lchsch_dbg_reg10    register"\n31:0    lchsch_dbg_reg10     ro          "Debug only"\n\n', 
 '%A  0x7b    "RXP_PKP lchsch_dbg_reg11    register"\n31:0    lchsch_dbg_reg11     ro          "Debug only"\n\n', 
 '%A  0x7c    "RXP_PKP lchsch_dbg_reg12    register"\n31:0    lchsch_dbg_reg12     ro          "Debug only"\n\n', 
 '%A  0x80    "RXP_PKP cqehdl_dbg_reg0    register"\n31:0    cqehdl_dbg_reg0     ro          "Debug only"\n\n', 
 '%A  0x81    "RXP_PKP cqehdl_dbg_reg1    register"\n31:0    cqehdl_dbg_reg1     ro          "Debug only"\n\n', 
 '%A  0x82    "RXP_PKP cqehdl_dbg_reg2    register"\n31:0    cqehdl_dbg_reg2     ro          "Debug only"\n\n', 
 '%A  0x83    "RXP_PKP cqehdl_dbg_reg3    register"\n31:0    cqehdl_dbg_reg3     ro          "Debug only"\n\n', 
 '%A  0x84    "RXP_PKP cqehdl_dbg_reg4    register"\n31:0    cqehdl_dbg_reg4     ro          "Debug only"\n\n', 
 '%A  0x85    "RXP_PKP cqehdl_dbg_reg5    register"\n31:0    cqehdl_dbg_reg5     ro          "Debug only"\n\n', 
 '%A  0x86    "RXP_PKP cqehdl_dbg_reg6    register"\n31:0    cqehdl_dbg_reg6     ro          "Debug only"\n\n', 
 '%A  0x87    "RXP_PKP cqehdl_dbg_reg7    register"\n31:0    cqehdl_dbg_reg7     ro          "Debug only"\n\n', 
 '%A  0x88    "RXP_PKP cqehdl_dbg_reg8    register"\n31:0    cqehdl_dbg_reg8     ro          "Debug only"\n\n', 
 '%A  0x89    "RXP_PKP cqehdl_dbg_reg9    register"\n31:0    cqehdl_dbg_reg9     ro          "Debug only"\n\n', 
 '%A  0x8a    "RXP_PKP cqehdl_dbg_reg10    register"\n31:0    cqehdl_dbg_reg10    ro          "Debug only"\n\n', 
 '%A  0x8b    "RXP_PKP cqehdl_dbg_reg11    register"\n31:0    cqehdl_dbg_reg11    ro          "Debug only"\n\n', 
 '%A  0x90    "RXP_PKP pkp_rqf_dbg_reg0   register"\n31:0    pkp_rqf_dbg_reg0        ro          "Debug only"\n\n', 
 '%A  0x91    "RXP_PKP pkp_rqf_dbg_reg1   register"\n31:0    pkp_rqf_dbg_reg1        ro          "Debug only"\n\n', 
 '%A  0x92    "RXP_PKP pkp_rqf_dbg_reg2   register"\n31:0    pkp_rqf_dbg_reg2        ro          "Debug only"\n\n', 
 '%A  0x93    "RXP_PKP pkp_rqf_dbg_reg3   register"\n31:0    pkp_rqf_dbg_reg3        ro          "Debug only"\n\n', 
 '%A  0x94    "RXP_PKP pkp_rqf_dbg_reg4   register"\n31:0    pkp_rqf_dbg_reg4        ro          "Debug only"\n\n', 
 '%A  0x95    "RXP_PKP pkp_rqf_dbg_reg5   register"\n31:0    pkp_rqf_dbg_reg5        ro          "Debug only"\n\n', 
 '%A  0x96    "RXP_PKP pkp_rqf_dbg_reg6   register"\n31:0    pkp_rqf_dbg_reg6        ro          "Debug only"\n\n', 
 '%A  0x97    "RXP_PKP pkp_rqf_dbg_reg7   register"\n31:0    pkp_rqf_dbg_reg7        ro          "Debug only"\n\n', 
 '%A  0x98    "RXP_PKP pkp_rqf_dbg_reg8   register"\n31:0    pkp_rqf_dbg_reg8        ro          "Debug only"\n\n', 
 '%A  0x99    "RXP_PKP pkp_rqf_dbg_reg9   register"\n31:0    pkp_rqf_dbg_reg9        ro          "Debug only"\n\n', 
 '%A  0x9a    "RXP_PKP pkp_rqf_dbg_reg10   register"\n31:0    pkp_rqf_dbg_reg10        ro          "Debug only"\n\n', 
 '%A  0x9b    "RXP_PKP pkp_rqf_dbg_reg11   register"\n31:0    pkp_rqf_dbg_reg11        ro          "Debug only"\n\n', 
 '%A  0x9c    "RXP_PKP pkp_rqf_dbg_reg12   register"\n31:0    pkp_rqf_dbg_reg12        ro          "Debug only"\n\n', 
 '%A  0x9d    "RXP_PKP pkp_rqf_dbg_reg13   register"\n31:0    pkp_rqf_dbg_reg13        ro          "Debug only"\n\n', 
 '%A  0x9e    "RXP_PKP pkp_rqf_dbg_reg14   register"\n31:0    pkp_rqf_dbg_reg14        ro          "Debug only"\n\n', 
 '%A  0x9f    "RXP_PKP pkp_rqf_dbg_reg15   register"\n31:0    pkp_rqf_dbg_reg15        ro          "Debug only"\n\n', 
 '%A  0xA0    "RXP_PKP pkp_duprd_dbg_reg0   register"\n31:0    pkp_duprd_dbg_reg0        ro          "Debug only"\n\n', 
 '%A  0xA1    "RXP_PKP pkp_duprd_dbg_reg1   register"\n31:0    pkp_duprd_dbg_reg1        ro          "Debug only"\n\n', 
 '%A  0xA2    "RXP_PKP pkp_duprd_dbg_reg2   register"\n31:0    pkp_duprd_dbg_reg2        ro          "Debug only"\n\n', 
 '%A  0xA3    "RXP_PKP pkp_duprd_dbg_reg3   register"\n31:0    pkp_duprd_dbg_reg3        ro          "Debug only"\n\n', 
 '%A  0xA4    "RXP_PKP pkp_duprd_dbg_reg4   register"\n31:0    pkp_duprd_dbg_reg4        ro          "Debug only"\n\n', 
 '%A  0xA5    "RXP_PKP pkp_duprd_dbg_reg5   register"\n31:0    pkp_duprd_dbg_reg5        ro          "Debug only"\n\n', 
 '%A  0xA6    "RXP_PKP pkp_duprd_dbg_reg6   register"\n31:0    pkp_duprd_dbg_reg6        ro          "Debug only"\n\n', 
 '%A  0xA7    "RXP_PKP pkp_duprd_dbg_reg7   register"\n31:0    pkp_duprd_dbg_reg7        ro          "Debug only"\n\n', 
 '%A  0xA8    "RXP_PKP pkp_duprd_dbg_reg8   register"\n31:0    pkp_duprd_dbg_reg8        ro          "Debug only"\n\n', 
 '%A  0xA9    "RXP_PKP pkp_duprd_dbg_reg9   register"\n31:0    pkp_duprd_dbg_reg9        ro          "Debug only"\n\n', 
 '%A  0xAA    "RXP_PKP pkp_duprd_dbg_reg10   register"\n31:0    pkp_duprd_dbg_reg10        ro          "Debug only"\n\n', 
 '%A  0xAB    "RXP_PKP pkp_duprd_dbg_reg11   register"\n31:0    pkp_duprd_dbg_reg11        ro          "Debug only"\n\n', 
 '%A  0xAC    "RXP_PKP pkp_duprd_dbg_reg12   register"\n31:0    pkp_duprd_dbg_reg12        ro          "Debug only"\n\n', 
 '%A  0xAD    "RXP_PKP pkp_duprd_dbg_reg13   register"\n31:0    pkp_duprd_dbg_reg13        ro          "Debug only"\n\n', 
 '%A  0xAE    "RXP_PKP pkp_duprd_dbg_reg14   register"\n31:0    pkp_duprd_dbg_reg14        ro          "Debug only"\n\n', 
 '%A  0xAF    "RXP_PKP pkp_duprd_dbg_reg15   register"\n31:0    pkp_duprd_dbg_reg15        ro          "Debug only"\n\n', 
 '%A  0x100   "rcqe_error_cnt register"\n31:0    rcqe_error_cnt      ro          "rcqe_error_cnt"\n\n', 
 '%A  0x101   "rcqe_flush_error_cnt register"\n31:0    rcqe_flush_error_cnt    ro          "rcqe_flush_error_cnt"\n\n', 
 '%A  0x110    "RXP_PKP pkp_rqf_dbg_reg16   register"\n31:0    pkp_rqf_dbg_reg16        ro          "Debug only"\n\n', 
 '%A  0x111    "RXP_PKP pkp_rqf_dbg_reg17   register"\n31:0    pkp_rqf_dbg_reg17        ro          "Debug only"\n\n', 
 '%A  0x112    "RXP_PKP pkp_rqf_dbg_reg18   register"\n31:0    pkp_rqf_dbg_reg18        ro          "Debug only"\n\n', 
 '%A  0x113    "RXP_PKP pkp_rqf_dbg_reg19   register"\n31:0    pkp_rqf_dbg_reg19        ro          "Debug only"\n'
]

for block in reg_block_list:
	if block.startswith('%A'):
		for line in block.splitlines():
			# field_lines = re.findall(
			# 	r'(\d+(?::\d+)?)\s+(\w+)\s+(\w+)\s+(0x[0-9a-fA-F]+)\s+"(.*?)"',
			# 	line, re.DOTALL
			# )
			field_lines = re.findall(
				r'(\d+(?::\d+)?)\s+'         # 位域
				r'(\w+)\s+'                  # 字段名
				r'(\w+)\s+'                  # 读写属性
				r'(?:'                      # 可选组开始（非捕获）
					r'(0x[0-9a-fA-F]+)\s+'  # 可选的复位值
				r')?'
				r'"(.*?)"',                 # 描述
				line,
				re.DOTALL
			)
			if field_lines:
				print(field_lines)



