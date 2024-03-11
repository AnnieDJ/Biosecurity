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

 Date: 10/03/2024 06:43:55
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for secureaccount
-- ----------------------------
DROP TABLE IF EXISTS `secureaccount`;
CREATE TABLE `secureaccount`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE,
  UNIQUE INDEX `email`(`email`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 27 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of secureaccount
-- ----------------------------
INSERT INTO `secureaccount` VALUES (1, 'KatherineFisher', 'f86ac60c30ec3f7a50206e3b94718ee0646a481b6f8bc2071ae79cbe58e110fd', 'Katherine@hotmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (2, 'JohnNguyen', 'd65c6e29b14c40c52247105b3d6bf811563a9f3322e3e106279c36ab7bfd7560', 'Nguyen@gmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (3, 'ErikaAnderson', 'cbee08fc85fc3a66cc9e7ec0c2842aca164040228a8b796f4323f478521cf3d9', 'Erika@gmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (4, 'CarrieJones', '1052bb5ee6278864dec2d7252848f9fe217554ca8205c603ed8f748914476492', 'Jones@hotmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (5, 'JorgeStrong', '9bd31d573aad725015a0b5285e60a50def88553703866db9c2f69f7242773ede', 'Strong@hotmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (6, 'BrittanyJohnson', '47b28f345756a2c675b69d75cdece70263d701ae0e9bb533823b5035aa7e4634', 'Brittany@hotmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (7, 'LisaGolden', 'd05edf9cd5245b9a8a032052cae639bf21e035a90343c38f9862e23943f97e0e', 'Golden@gmail.com', 'Gardener user');
INSERT INTO `secureaccount` VALUES (8, 'AliceJohnson', '983487d9c4b7451b0e7d282114470d3a0ad50dc5e554971a4d1cda04acde670b', 'alice.johnson@gmail.com', 'Staff');
INSERT INTO `secureaccount` VALUES (9, 'BobSmith', '983487d9c4b7451b0e7d282114470d3a0ad50dc5e554971a4d1cda04acde670b', 'bob.smith@gmail.com', 'Administration');
INSERT INTO `secureaccount` VALUES (10, 'CharlieDavis', '3c5521128036d1ca0687fafa919e025c461134fc5840963127c7e0c204c3eb78', 'charlie.davis@gmail.com', 'Staff');
INSERT INTO `secureaccount` VALUES (11, 'DianaMartinez', '09e4d427fe8e84ad748ad79e91fbd95c426a517bae8e472a8a4965135de6728d', 'diana.martinez@gmail.com', 'Staff');
INSERT INTO `secureaccount` VALUES (12, 'Annie', '983487d9c4b7451b0e7d282114470d3a0ad50dc5e554971a4d1cda04acde670b', 'Annie@gmail.com', 'Gardener user');

SET FOREIGN_KEY_CHECKS = 1;
