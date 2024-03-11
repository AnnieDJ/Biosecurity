/*
 Navicat Premium Data Transfer

 Source Server         : root
 Source Server Type    : MySQL
 Source Server Version : 80036
 Source Host           : localhost:3306
 Source Schema         : biosecurity_guide

 Target Server Type    : MySQL
 Target Server Version : 80036
 File Encoding         : 65001

 Date: 10/03/2024 06:42:54
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for gardner_profile
-- ----------------------------
DROP TABLE IF EXISTS `gardner_profile`;
CREATE TABLE `gardner_profile`  (
  `ID` int NOT NULL AUTO_INCREMENT,
  `secureaccount_id` int NULL DEFAULT NULL,
  `First_Name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Last_Name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Phone_Number` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Date_Joined` datetime NULL DEFAULT NULL,
  `Status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `fk_secureaccount_id`(`secureaccount_id`) USING BTREE,
  CONSTRAINT `fk_secureaccount_id` FOREIGN KEY (`secureaccount_id`) REFERENCES `secureaccount` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 24014 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of gardner_profile
-- ----------------------------
INSERT INTO `gardner_profile` VALUES (24001, 1, 'Katherine232', 'Fisher34321', '4759 William Haven Apt,TX 43780', 'Katherine@hotmail.com', '229842984123', '2022-09-16 00:00:00', 'Active');
INSERT INTO `gardner_profile` VALUES (24002, 2, 'John', 'Nguyen', '332 Davis Island, Rodriguezside, VT 16860', 'Nguyen@gmail.com', '249749823', '2020-07-19 00:00:00', 'Active');
INSERT INTO `gardner_profile` VALUES (24003, 3, 'Erika', 'Anderson', '86848 Melissa Springs, Rileymouth, TN 84543', 'Erika@gmail.com', '207891567', '2021-12-09 00:00:00', 'Inactive');
INSERT INTO `gardner_profile` VALUES (24004, 4, 'Carrie', 'Jones', '916 Mitchell Crescent, New Andrewburgh, DE 63315', 'Jones@hotmail.com', '216532837', '2019-12-16 00:00:00', 'Active');
INSERT INTO `gardner_profile` VALUES (24005, 5, 'Jorge', 'Strong', '302 Matthew Glen, New Sandraburgh, NJ 89797', 'Strong@hotmail.com', '264752084', '2021-11-22 00:00:00', 'Inactive');
INSERT INTO `gardner_profile` VALUES (24006, 6, 'Brittany', 'Johnson', '466 Aaron Fields, Ernestbury, NV 50131', 'Brittany@hotmail.com', '230989023', '2023-10-15 00:00:00', 'Active');
INSERT INTO `gardner_profile` VALUES (24007, 7, 'Lisa', 'Golden', '120 Herring Mall, Aarontown, WV 00810', 'Golden@gmail.com', '223041638', '2023-07-01 00:00:00', 'Active');
INSERT INTO `gardner_profile` VALUES (24008, 12, 'Annie', 'Dou', '124 Herring Mall, Aarontown, WV 00810', 'Annie@gmail.com', '2230413285', '2023-07-07 00:00:00', 'Active');

SET FOREIGN_KEY_CHECKS = 1;
