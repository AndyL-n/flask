-- 回滚此前导入脚本新增的五张辅助表。
-- 提供的服务器结构中，原业务表字段/索引未被此前脚本修改，无需ALTER TABLE。
-- 此脚本只删除以下五张辅助表及其中备份，不删除业务表或业务数据。
-- 若旧导入已成功且需要恢复导入前数据，应先使用旧版配套数据回滚文件再执行本文件。
-- DDL即时提交；删除辅助表不支持事务恢复。目标数据库jdf。
-- 每条语句明确指定jdf，避免phpMyAdmin当前数据库上下文影响。
-- 如果服务器库名不同，请替换下面所有 `jdf`。

DROP TABLE IF EXISTS `jdf`.`_jdf_yanchang_backup_device`;

DROP TABLE IF EXISTS `jdf`.`_jdf_yanchang_backup_pole`;

DROP TABLE IF EXISTS `jdf`.`_jdf_yanchang_backup_site`;

DROP TABLE IF EXISTS `jdf`.`_jdf_yanchang_import_rows`;

DROP TABLE IF EXISTS `jdf`.`_jdf_yanchang_import_meta`;

SHOW TABLES FROM `jdf`;
