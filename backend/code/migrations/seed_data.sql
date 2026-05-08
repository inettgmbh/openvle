-- Seed data for OpenVLE
-- Order respects foreign key dependencies

-- sys_users
INSERT INTO `sys_users` (`username`, `name`, `email`, `hashed_password`, `resetToken`, `resetTokenCreatedAt`, `status`, `locale`, `twoFactorSecret`, `mailValidateToken`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('system', 'System Benutzer', 'system@system.system', NULL, NULL, NULL, 'Active', 'en_US', NULL, NULL, '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('openvle', 'Default Administrator', 'openvle@example.com', '$2b$12$sbW6FYPehAomGkWlxsTWyOS3ipRw0erIsQrXLtQ/xLMhtPOJqitJm', NULL, NULL, 'Active', 'de_DE', NULL, NULL, '71803f9c-b97b-4dd4-999f-f55084666d12', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- kvs_vendors
INSERT INTO `kvs_vendors` (`name`, `description`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Canonical Foundation', 'Sponsor der kostenlosen Debian-basierten Linux-Distribution Ubuntu', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Apple Inc', 'US-amerikanischer Hard- und Softwareentwickler', 'f8623d23-c2a9-496a-9e3f-110cee0af7f4', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Das Debian-Projekt', 'Gemeinschaftlich entwickeltes freies Betriebssystem', '47812777-8dbf-4916-be13-37db94aa4a2a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Atlassian', 'Anbieter von Softwarelösungen', 'cb504c69-9157-4241-9fed-4789a81f1c1d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Microsoft', 'US-amerikanischer Hard- und Softwareentwickler', 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Mozilla', 'Gemeinnützige Organisation hinter Firefox', '615fbf29-efc9-4910-a11c-616191bc1959', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Adobe Inc', 'US-amerikanischer Softwareentwickler', '85d37e92-8e20-4521-a657-71f46be0b45d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('inett GmbH', 'Linux und Open Source Software für Unternehmen', 'fe3d0fb0-9025-4261-b7ae-8289a79c7497', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Google', 'US-amerikanisches Technologieunternehmen', '86bd4297-3ce2-4745-b9dc-b2c4960f2c10', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- kvs_apps
INSERT INTO `kvs_apps` (`key`, `name`, `patch_level`, `description`, `vendor`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('powerpoint_2022', 'PowerPoint 2022', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '98bfd7be-d83a-42dc-b16b-076dc96f2e96', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('visual_studio_code', 'Visual Studio Code', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '2aab6a3e-a322-4f98-8095-0f6e6de4fc44', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('photoshop', 'Photoshop', NULL, NULL, '85d37e92-8e20-4521-a657-71f46be0b45d', 'c0e5fb9b-c682-41a2-903e-130d22fd5db7', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('powerpoint_2020', 'PowerPoint 2020', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '4dcec96b-58f1-45a1-bb3e-455fb4a251ca', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('chrome', 'Chrome', NULL, NULL, '86bd4297-3ce2-4745-b9dc-b2c4960f2c10', '2359089d-61bc-4296-901e-5ca17b3f6135', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('word_2022', 'Word 2022', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '51c1cbe3-53fa-4db2-8446-7c91a9de37a0', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('excel_2022', 'Excel 2022', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '6c6b9845-a462-42c9-8e30-9ddedaae839f', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('excel_2020', 'Excel 2020', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', 'bc6714d3-280b-4cef-8387-a7be20eee0a7', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('firefox', 'Firefox', NULL, NULL, '615fbf29-efc9-4910-a11c-616191bc1959', 'f7fc2362-9717-4127-80bc-bfa0b5b216b6', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('word_2020', 'Word 2020', NULL, NULL, 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', 'adaa1e92-2a79-4e0b-a962-d7e0a6f28bb0', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- kvs_os
INSERT INTO `kvs_os` (`name`, `key`, `patch_level`, `description`, `version`, `vendor`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Debian 11 Bullseye', 'debian_11_bullseye', NULL, NULL, '11', '47812777-8dbf-4916-be13-37db94aa4a2a', '0d9e7dac-50ff-487f-9420-120f16bb8df5', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Windows 10', 'windows_10', NULL, NULL, '10', 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '109a1e59-216d-4a68-8ade-362c1669feaa', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Debian 10 Buster', 'debian_10_buster', NULL, NULL, '10', '47812777-8dbf-4916-be13-37db94aa4a2a', 'dca56dbc-ff90-4e43-a3d8-47d051fc406a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('macOS 14 Sonoma', 'macos_14_sonoma', NULL, NULL, '14', 'f8623d23-c2a9-496a-9e3f-110cee0af7f4', 'eb75c306-eab6-4170-a205-4b63f1c7b26e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Ubuntu 20.04 LTS', 'ubuntu_20_04_lts', NULL, NULL, '2004', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '8fae042b-81a9-44a3-9572-4b7a8c06ba89', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Debian 12 Bookworm', 'debian_12_bookworm', NULL, NULL, '12', '47812777-8dbf-4916-be13-37db94aa4a2a', 'bdda06a1-486c-491e-9d44-5d23189b08c3', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Ubuntu 23.04', 'ubuntu_23_04', NULL, NULL, '2304', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '43adb932-2438-4005-b0bd-7d9e3afbd757', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Windows 11', 'windows_11', NULL, NULL, '11', 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', 'f6843793-240e-42b0-ae45-8162952d4e5d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Windows 7', 'windows_7', NULL, NULL, '7', 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', '17007f1a-4073-4add-b41d-90dab8306ef2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('macOS 13 Ventura', 'macos_13_ventura', NULL, NULL, '13', 'f8623d23-c2a9-496a-9e3f-110cee0af7f4', '0f74f154-54fe-469d-b708-99d887cab040', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Windows 8', 'windows_8', NULL, NULL, '8', 'b2bff1ed-1c4f-4739-aa4d-4beebaf3bbb5', 'ec4aa76c-3f7a-4cb8-bbd4-abb1f589a291', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Ubuntu 22.04 LTS', 'ubuntu_22_04_lts', NULL, NULL, '2204', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '27d5e8ba-8205-4d6d-9934-d16c63265d75', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Ubuntu 22.10', 'ubuntu_22_10', NULL, NULL, '2210', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '30398d64-77cd-41db-bbc2-e2b7f65649b0', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Ubuntu 21.04', 'ubuntu_21_04', NULL, NULL, '2104', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '195e5299-4931-4db3-8800-f904b2270bdc', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Ubuntu 21.10', 'ubuntu_21_10', NULL, NULL, '2110', 'c5a24ba9-ba6e-4bdc-8947-001a019e95c4', '2407f857-1453-4184-b494-fe05bf43aeee', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- sys_roles
INSERT INTO `sys_roles` (`name`, `description`,`key`, `protected`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Administrator (Read Only)', 'Contains all permissions', 'admin_read_only', 1, '374568c9-feb7-4741-a74e-07ef8fe80050', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Administrator (Full)', 'Contains all permissions', 'admin_full', 1, 'd8d8de51-0242-4453-bda4-cb53cc832dd3', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Lehrende', 'Standard Rolle für Lehrende der Kurse', 'lehrende', 1, 'acec4438-2dec-41fb-9e5e-f0284845753e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Studierende', 'Standard Rolle für Studierende der Kurse', 'studierende', 1, 'cec850b3-608b-4cc3-aac2-4adc85df38e3', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- sys_languages
INSERT INTO `sys_languages` (`nameEnglish`, `nameTranslated`, `key`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Croatian (Croatia)', 'Hrvatski (Hrvatska)', 'hr_HR', '130852f0-67d4-4eb0-9886-0e85b071c784', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Swedish (Sweden)', 'Svenska (Sverige)', 'sv_SE', 'd95eaae4-d4d7-4d9c-9996-18d90da6d343', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('English (United Kingdom)', 'English (United Kingdom)', 'en_GB', 'c4a50d3d-3903-4e01-bc26-1c2f7ff84d31', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Spanish (Spain)', 'Español (España)', 'es_ES', '1a7f54dd-5dcf-48a0-9142-26e292f78cc5', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Finnish (Finland)', 'Suomi (Suomi)', 'fi_FI', '8988182c-3f18-4b5c-9c6f-2f89c9d2a450', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Finnish (Åland Islands)', 'Suomi (Ahvenanmaa)', 'fi_AX', '06675f1d-5c47-4a46-95a3-3d3efdc7e4e1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Greek (Greece)', 'Ελληνικά (Ελλάδα)', 'el_GR', '50ff792b-8e36-4e68-bc6f-3f399b51f089', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('French (France)', 'Français (France)', 'fr_FR', '3c8efcf6-35e4-49b1-a002-4309b4f5981c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Polish (Poland)', 'Polski (Polska)', 'pl_PL', '2eddb68f-3803-41af-b79a-4b70d0d2efc0', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Estonian (Estonia)', 'Eesti (Eesti)', 'et_EE', 'f0a178d4-89d7-46b4-9504-4bc057779dfb', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Dutch (Netherlands)', 'Nederlands (Nederland)', 'nl_NL', 'be3175bf-9e45-4e60-82da-4e5a835754b7', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Slovenian (Slovenia)', 'Slovenščina (Slovenija)', 'sl_SI', '92f60ca5-4ad9-4826-9e45-5db6f35b3e3e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Spanish (Mexico)', 'Español (México)', 'es_MX', '52268e32-7862-4c13-bb42-5e5d1d52af62', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Czech (Czech Republic)', 'Čeština (Česká republika)', 'cs_CZ', '110cfa34-7a24-4477-8714-60bc067a8657', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('German (Germany)', 'Deutsch (Deutschland)', 'de_DE', '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Bulgarian (Bulgaria)', 'Български (България)', 'bg_BG', 'fc1950f1-b540-47a1-9b10-865c77f0e12c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Irish (Ireland)', 'Gaeilge (Éire)', 'ga_IE', '9a6cbf45-df33-48a3-a5eb-8b37f10d5b7b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Latvian (Latvia)', 'Latviešu (Latvija)', 'lv_LV', 'ad433d4c-869c-46c5-b09e-91427be9c8f4', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('French (Canada)', 'Français (Canada)', 'fr_CA', '0e1680b2-dc11-4fb5-ba25-9250de8a468a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Danish (Denmark)', 'Dansk (Danmark)', 'da_DK', 'b0c754b2-29d0-4347-9ce3-95a8ab3a962b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('English (United States)', 'English (United States)', 'en_US', '1e5d9433-0db2-4e15-8c81-979447a8a0c6', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Romanian (Romania)', 'Română (România)', 'ro_RO', '84a7251c-61d1-4d3e-9e25-9c40ee8e3e7b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Lithuanian (Lithuania)', 'Lietuvių (Lietuva)', 'lt_LT', 'cb4f5f3d-9a3d-4e13-81d6-9eef12bf1002', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Hungarian (Hungary)', 'Magyar (Magyarország)', 'hu_HU', 'd2cf47e4-b36d-42df-9746-b47c283bb20e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Slovak (Slovakia)', 'Slovenčina (Slovenská republika)', 'sk_SK', '71b22b75-7a12-46e5-b3ce-d07e4d5da58c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Portuguese (Portugal)', 'Português (Portugal)', 'pt_PT', '27efdb4e-aa62-40b5-8ef3-d0cb6314f7b2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Maltese (Malta)', 'Malti (Malta)', 'mt_MT', '38372675-0c89-41b4-b1d5-d3f07c0bbabe', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Italian (Italy)', 'Italiano (Italia)', 'it_IT', 'd5d85ac0-3b1f-4c77-8f3c-efbc1e7b64e1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- kvs_events_status
INSERT INTO `kvs_events_status` (`name`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Aktiv', 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Inaktiv', 'cbc20092-629b-483f-babc-ef26202d685e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Archiviert', 'bfbee14d-6f04-4ba1-a39c-0f5764f0563d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Stopped', '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Deploying', 'f13303bf-b25f-4869-9717-698a4db13ada', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Archiving', '4d99fe64-3c3c-4a2f-99fe-643c3c1a2f23', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Deployment Fehler', 'e5c9fafd-c5ec-4aa5-89fa-fdc5ec0aa595', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Archival Fehler', 'af12d859-9aa6-4fae-92d8-599aa6ffae93', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Core Fehler', 'f63a9362-eb67-4769-ba93-62eb67b76939', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Geplant', '53b6993a-57d6-40a6-8d42-e55bf08fac4c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- sys_object_permissions
INSERT INTO `sys_object_permissions` (`object_type`, `object_id`, `entity_type`, `entity_id`, `permission_key`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Activity', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', 'bc13291c-c437-4179-a4ac-f56df3b55b97', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Application', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '1e1c9e64-7825-477e-a3ba-1916c8a498b7', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Changelog', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '7936e48a-aec3-43cf-b6e4-8aaec313cf77', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Course', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '0f1f9357-6283-4eeb-a903-6ad156c2075c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Dashboard', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_admins', 'b033945f-0459-4197-b8a7-cdf78b982ee1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Document', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '55ad69cc-8aae-49d7-97a9-fb9e4c6c9d60', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Event', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '169d0242-d79d-422a-9a25-c8d078c86f6a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Guacamole', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', 'f2d2f7e2-5d06-4b05-96ba-9394ffab63ec', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('GuacamoleConnectionProfile', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '7cfe1d45-2388-4bd0-a5f6-cf2c4fbf8a00', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Mail', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '71c9c4e8-9247-44eb-97f6-dd49b6c9d8eb', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('MailTemplate', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '8b7a4748-b35c-4467-bd20-10ca3550213a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('ObjectPermission', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '1d36d20b-2a75-412a-a25e-7b7f2416dfbb', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('OS', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '8cf079fd-e19e-4fe9-995b-24e1bd39e908', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Policy', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '0dcd5d67-c8d3-4114-96c1-eff017ed93e9', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Proxmox', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '53438430-cc05-4c06-8384-30cc052c061e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Role', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '9d3646b6-d7ca-4055-a2fa-7a655fbd259b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('SubTask', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', 'b7b287da-b5f1-40a1-96b4-c5b3df64d439', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('System', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', 'b64593eb-1383-4f58-8593-eb13834f581b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Task', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', 'd26ff339-b319-412a-bcb3-4d8941cd39eb', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Template', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '701d3ace-1a55-4255-9eba-b0a8162c3e3a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('User', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '2c00e8db-af14-49ba-b8e4-0168bc4a209d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Vendor', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '5d31c358-05ca-4045-9dee-e39dfe55d8ad', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('VirtualMachine', NULL, 'Role', 'd8d8de51-0242-4453-bda4-cb53cc832dd3', 'object_full', '072e05a4-26bd-4735-9fe5-a719a7f901d8', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Activity', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '0c1d9b12-2f2e-49d1-9d9b-122f2e39d1ac', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Application', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '9d1d767d-1a05-4d63-9ea5-6df531f60c9f', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Changelog', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', 'ca8eb332-f4ee-44c8-8eb3-32f4ee54c8ce', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Course', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '5e7676a2-fcf3-46c2-acfe-c68160524d35', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Dashboard', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_admins', '50474f7f-6166-4cd3-874f-7f61661cd33c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Document', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '1a5b5505-827a-482b-91ed-944c2812a3d2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Event', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '1fd83eb1-9269-40a6-a2f4-cd4606269862', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Guacamole', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', 'ef8abff1-05d6-48f1-80ad-54e1bd253517', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('GuacamoleConnectionProfile', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '2c087a6b-029e-4c40-b583-ea46c0e3cb07', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Mail', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', 'fe67ea3c-200f-43ec-a063-43959e58dcac', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('MailTemplate', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '8afbb6f5-9567-40e8-b12d-28100a05c903', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('ObjectPermission', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '5769f5bb-0d5d-4e7a-8425-07f873330d60', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('OS', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '723f6741-d2f8-41cb-8bda-a4de18619b1c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Policy', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '8091e293-a3c5-4910-87f7-2c8003ca2f81', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Proxmox', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '38c49b37-3fec-4c5c-849b-373fec9c5cca', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Role', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', 'd1a284bd-f69f-4f2d-af2a-2aa06174c15d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('SubTask', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', 'accef6b9-d7f9-417d-ad84-cae7e728b7bd', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('System', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '82209f43-644c-4184-a09f-43644c318481', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Task', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', 'dca96a1e-c0ec-473f-b156-fa54b9b27a31', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Template', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '93ef7488-acd1-4c8b-a073-2220b23bfb8a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('User', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '837403e7-47eb-40de-aa7f-24ad46649e6c', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Vendor', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '1be7f635-be7c-433d-aebb-fc7d886ef653', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('VirtualMachine', NULL, 'Role', '374568c9-feb7-4741-a74e-07ef8fe80050', 'object_read', '3b7c2c4b-aa3c-4a20-aa6e-c9714640e62b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- sys_users_roles
INSERT INTO `sys_users_roles` (`user_id`, `role_id`) VALUES
('71803f9c-b97b-4dd4-999f-f55084666d12', 'd8d8de51-0242-4453-bda4-cb53cc832dd3');

-- sys_mails_actions
INSERT INTO `sys_mails_actions` (`name`, `description`, `slug`, `id`, `createdAt`, `updatedAt`, `createdById`, `updatedById`) VALUES
('Veranstaltung erfolgreich bereitgestellt', 'Benachrichtigt alle Teilnehmenden (Lehrende und Studierende), dass die Veranstaltung erfolgreich bereitgestellt wurde und nun verfügbar ist.', 'events_post_deployment_success', 'dc619c3f-53ae-4c0c-a19c-3f53ae8c0c0e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung konnte nicht archiviert werden', 'Informiert die Veranstaltungs-Admins, dass die Archivierung der Veranstaltung fehlgeschlagen ist und manuelle Maßnahmen erforderlich sein könnten.', 'events_post_decommission_failed', '822195df-4844-432e-a195-df4844732e48', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung konnte nicht bereitgestellt werden', 'Benachrichtigt die Veranstaltungs-Admins, dass die Bereitstellung der Veranstaltung fehlgeschlagen ist. Enthält ggf. technische Details oder Hinweise zur Fehlerbehebung.', 'events_post_deployment_failed', '58d9f3cb-eecd-4c20-99f3-cbeecd1c20f1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird archiviert', 'Informiert alle Teilnehmenden (Lehrende und Studierende), dass die Veranstaltung derzeit archiviert wird und nicht mehr zugänglich sein wird.', 'events_decommission_started', '76842db4-c0ee-44aa-842d-b4c0ee24aab5', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird bald beginnen', 'Sendet eine Erinnerung an alle Teilnehmenden (Lehrende und Studierende), dass die Veranstaltung in Kürze startet. Enthält ggf. Zugangsdaten oder organisatorische Hinweise.', 'events_pre_start', '47c73a0f-acef-4990-873a-0facefd9905a', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird bereitgestellt', 'Informiert die Veranstaltungs-Admins, dass die Bereitstellung der Veranstaltung begonnen hat. Dient zur Statusverfolgung der Bereitstellung.', 'events_deployment_started', 'd8bddb6f-ba96-4367-bddb-6fba96d367cf', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird demnächst archiviert (Lehrende)', 'Benachrichtigt nur die Lehrenden, dass die Veranstaltung demnächst archiviert wird, mit der Möglichkeit, vorab noch letzte Änderungen oder Downloads vorzunehmen.', 'events_pre_end_admin', 'bdb41031-f531-43b6-b410-31f531f3b6aa', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird demnächst archiviert (Studierende)', 'Informiert nur die Studierenden, dass die Veranstaltung bald archiviert wird und Material oder Ergebnisse vorher gesichert werden sollten.', 'events_pre_end_student', '83fb7d48-19cd-491d-bb7d-4819cd691db6', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung erfolgreich archiviert', 'Bestätigt den Veranstaltungs-Admins, dass die Archivierung erfolgreich abgeschlossen wurde.', 'events_post_decommission_success', 'd06f1781-ff2c-415f-af17-81ff2cc15fe9', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung erfolgreich gelöscht', 'Benachrichtigt die Veranstaltungs-Admins, dass die Veranstaltung vollständig gelöscht wurde. Enthält ggf. Bestätigungs- oder Log-Informationen.', 'events_delete', '5d57abde-4ac0-4236-97ab-de4ac02236e0', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine konnte nicht bereitgestellt werden', 'Informiert, dass eine virtuelle Maschine während der Bereitstellung nicht erstellt werden konnte. Enthält technische Fehlerdetails.', 'vm_create_failed', 'd2d9f5a9-32b8-4499-99f5-a932b814997b', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine konnte nicht gelöscht werden', 'Benachrichtigt dass das Löschen einer virtuellen Maschine fehlgeschlagen ist. Ggf. mit Hinweisen zur manuellen Bereinigung.', 'vm_delete_failed', '44343eda-b62a-4f04-b43e-dab62a3f044d', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine wird gelöscht', 'Sendet eine Statusmeldung, dass der Löschvorgang einer virtuellen Maschine gestartet wurde.', 'vm_delete_started', '5822b860-f6a5-4c47-a2b8-60f6a50c47d1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine erfolgreich bereitgestellt', 'Benachrichtigt, dass die virtuelle Maschine erfolgreich erstellt und einsatzbereit ist.', 'vm_create_success', '5491d02c-e23c-4e64-91d0-2ce23cce64c6', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- sys_mails_templates
INSERT INTO `sys_mails_templates` (`name`, `subject`, `description`, `fromName`, `fromMail`, `contentHTML`, `contentPlain`, `language`, `protected`, `replyTo`, `mail_action`,`id`,`createdAt`,`updatedAt`,`createdById`,`updatedById`) VALUES
('Virtuelle Maschine wurde erfolgreich bereitgestellt', 'Virtuelle Maschine wurde erfolgreich bereitgestellt', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: vm_create_success', NULL, NULL,
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} wurde erfolgreich bereitgestellt',
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} wurde erfolgreich bereitgestellt',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '5491d02c-e23c-4e64-91d0-2ce23cce64c6','49388f61-80de-4c3d-b88f-6180de5c3d63','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine konnte nicht bereitgestellt werden', 'Virtuelle Maschine konnte nicht bereitgestellt werden', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: vm_create_failed', NULL, NULL,
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} konnte nicht bereitgestellt werden',
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} konnte nicht bereitgestellt werden',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, 'd2d9f5a9-32b8-4499-99f5-a932b814997b','35263f88-0cd8-4ed6-a63f-880cd88ed63a','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine wird gelöscht', 'Virtuelle Maschine wird gelöscht', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: vm_delete_started', NULL, NULL,
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} wird gelöscht',
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} wird gelöscht',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '5822b860-f6a5-4c47-a2b8-60f6a50c47d1','f50be2e1-19e9-4122-8be2-e119e9c122fa','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Virtuelle Maschine konnte nicht gelöscht werden', 'Virtuelle Maschine konnte nicht gelöscht werden', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: vm_delete_failed', NULL, NULL,
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} konnte nicht gelöscht werden',
 'Virtuelle Maschine mit Name: {{ virtualmachine.name }} konnte nicht gelöscht werden',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '44343eda-b62a-4f04-b43e-dab62a3f044d','eb8e1440-013c-4872-8e14-40013c887210','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird bereitgestellt', 'Veranstaltung wird bereitgestellt', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_deployment_started', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wird bereitgestellt',
 'Veranstaltung mit dem Namen {{ event.name }} wird bereitgestellt',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, 'd8bddb6f-ba96-4367-bddb-6fba96d367cf','68b0bcd1-8d0d-4ec5-b0bc-d18d0deec53d','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung erfolgreich bereitgestellt', 'Veranstaltung erfolgreich bereitgestellt', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_post_deployment_success', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wurde erfolgreich bereitgestellt',
 'Veranstaltung mit dem Namen {{ event.name }} wurde erfolgreich bereitgestellt',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, 'dc619c3f-53ae-4c0c-a19c-3f53ae8c0c0e','d2901446-fabe-4d57-9014-46fabe5d5716','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung konnte nicht bereitgestellt werden', 'Veranstaltung konnte nicht bereitgestellt werden', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_post_deployment_failed', NULL, NULL,
 'Die Post-Deployment-Aufgabe Ihrer Veranstaltung ist fehlgeschlagen.
Veranstaltungsdetails
- Name: {{ event.name }}
- Beschreibung: {{ event.description }}
- Start: {{ event.dateStart }} {{ event.timeStart }}
- Ende: {{ event.dateEnd }} {{ event.timeEnd }}

Fehlerdetails
- Aufgabe: {{ subtask.name }} ({{ subtask.action }})
- Status: {{ subtask.status }} (Versuch {{ subtask.attempt }})
- Code: {{ subtask.response_code }}
- Meldung: {{ subtask.response_message }}
- Job-ID: {{ subtask.job_id }}',
 'die Post-Deployment-Aufgabe Ihrer Veranstaltung ist fehlgeschlagen.
Veranstaltungsdetails
- Name: {{ event.name }}
- Beschreibung: {{ event.description }}
- Start: {{ event.dateStart }} {{ event.timeStart }}
- Ende: {{ event.dateEnd }} {{ event.timeEnd }}

Fehlerdetails
- Aufgabe: {{ subtask.name }} ({{ subtask.action }})
- Status: {{ subtask.status }} (Versuch {{ subtask.attempt }})
- Code: {{ subtask.response_code }}
- Meldung: {{ subtask.response_message }}
- Job-ID: {{ subtask.job_id }}',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '58d9f3cb-eecd-4c20-99f3-cbeecd1c20f1','ae066e73-1b6a-4f81-866e-731b6a7f811b','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird archiviert', 'Veranstaltung wird archiviert', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_decommission_started', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wird archiviert',
 'Veranstaltung mit dem Namen {{ event.name }} wird archiviert',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '76842db4-c0ee-44aa-842d-b4c0ee24aab5','d8e53874-1d77-47eb-a538-741d77b7ebdc','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wurde erfolgreich archiviert', 'Veranstaltung wurde erfolgreich archiviert', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_post_decommission_success', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wurde erfolgreich archiviert',
 'Veranstaltung mit dem Namen {{ event.name }} wurde erfolgreich archiviert',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, 'd06f1781-ff2c-415f-af17-81ff2cc15fe9','811d63db-d3ab-46bc-9d63-dbd3ab96bc8d','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung konnte nicht archiviert werden', 'Veranstaltung konnte nicht archiviert werden', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_post_decommission_failed', NULL, NULL,
 'Die Post-Decommission-Aufgabe Ihrer Veranstaltung ist fehlgeschlagen.

Veranstaltungsdetails
- Name: {{ event.name }}
- Beschreibung: {{ event.description }}
- Start: {{ event.dateStart }} {{ event.timeStart }}
- Ende: {{ event.dateEnd }} {{ event.timeEnd }}

Fehlerdetails
- Aufgabe: {{ subtask.name }} ({{ subtask.action }})
- Status: {{ subtask.status }} (Versuch {{ subtask.attempt }})
- Code: {{ subtask.response_code }}
- Meldung: {{ subtask.response_message }}
- Job-ID: {{ subtask.job_id }}

Hinweis: Teile der Infrastruktur könnten weiterhin aktiv sein, bis die Decommission erfolgreich abgeschlossen wurde.',
 'Die Post-Decommission-Aufgabe Ihrer Veranstaltung ist fehlgeschlagen.

Veranstaltungsdetails
- Name: {{ event.name }}
- Beschreibung: {{ event.description }}
- Start: {{ event.dateStart }} {{ event.timeStart }}
- Ende: {{ event.dateEnd }} {{ event.timeEnd }}

Fehlerdetails
- Aufgabe: {{ subtask.name }} ({{ subtask.action }})
- Status: {{ subtask.status }} (Versuch {{ subtask.attempt }})
- Code: {{ subtask.response_code }}
- Meldung: {{ subtask.response_message }}
- Job-ID: {{ subtask.job_id }}

Hinweis: Teile der Infrastruktur könnten weiterhin aktiv sein, bis die Decommission erfolgreich abgeschlossen wurde.',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '822195df-4844-432e-a195-df4844732e48','ddff06f3-78ef-46d9-bf06-f378ef36d915','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wurde gelöscht', 'Veranstaltung wurde gelöscht', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_delete', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wurde gelöscht',
 'Veranstaltung mit dem Namen {{ event.name }} wurde gelöscht',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '5d57abde-4ac0-4236-97ab-de4ac02236e0','57d64513-b370-46a3-9645-13b370f6a3c2','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird bald beginnen', 'Veranstaltung wird bald beginnen', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_pre_start', NULL, NULL,
 'Das Veranstaltung mit dem Namen {{ event.name }} wird demnächst bereitgestellt.',
 'Das Veranstaltung mit dem Namen {{ event.name }} wird demnächst bereitgestellt.',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '47c73a0f-acef-4990-873a-0facefd9905a','542cc480-3dc3-4b75-acc4-803dc3cb75e6','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird demnächst archiviert (Lehrende)', 'Veranstaltung wird demnächst archiviert', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_pre_end_admin', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wird demnächst archiviert.',
 'Veranstaltung mit dem Namen {{ event.name }} wird demnächst archiviert.',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, 'bdb41031-f531-43b6-b410-31f531f3b6aa','25d68eec-1cbe-42b1-968e-ec1cbe62b1db','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234'),
('Veranstaltung wird demnächst archiviert (Studierende)', 'Veranstaltung wird demnächst archiviert', 'Mail-Vorlage für systemgesteuerte Mail-Aktion: events_pre_end_student', NULL, NULL,
 'Veranstaltung mit dem Namen {{ event.name }} wird demnächst archiviert. Alle dazugehörigen virtuellen Maschinen werden am {{ event.dateEnd }} außer Betrieb genommen.',
 'Veranstaltung mit dem Namen {{ event.name }} wird demnächst archiviert. Alle dazugehörigen virtuellen Maschinen werden am {{ event.dateEnd }} außer Betrieb genommen.',
 '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0', 1, NULL, '83fb7d48-19cd-491d-bb7d-4819cd691db6','9daacdf5-4b4b-437e-aacd-f54b4bd37ea1','1970-01-01 00:00:00','1970-01-01 00:00:00','1db3d8ac-22d9-4116-976a-93ad6e4fb234','1db3d8ac-22d9-4116-976a-93ad6e4fb234');

-- sys_settings
INSERT INTO `sys_settings` (`key`, `value`, `createdAt`, `updatedAt`, `createdById`, `updatedById`, `id`, `visibility`, `description`) VALUES
('auth.ldap.enabled', 'false', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'f9757bca-40c3-4c50-a8ec-ed53cf9bf147', 'admins', 'Gibt an, ob LDAP-Authentifizierung aktiviert ist'),
('auth.local.enabled', 'true', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '68d8ab54-90aa-40d4-ae0c-f7cb31136d82', 'public', 'Gibt an, ob lokale Benutzeranmeldung erlaubt ist'),
('auth.local.username.help', 'Bitte geben Sie Ihren Benutzernamen ein', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'd486d70b-0798-40ce-bdbc-929af335ab2d', 'public', 'Hilfetext für das Benutzername-Feld beim lokalen Login'),
('auth.local.password.help', 'Bitte geben Sie Ihr Passwort ein', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '4a99d23c-2e40-4e19-a238-f5d6f7d6189c', 'public', 'Hilfetext für das Passwort-Feld beim lokalen Login'),
('auth.oidc.enabled', 'false', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'ceabb4fd-bd8a-41fc-809d-31c44532bd0b', 'public', 'Gibt an, ob OpenID Connect-Login aktiviert ist'),
('auth.oidc.label', '', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '52460396-4a09-49f1-97f9-c8256b5d97fd', 'public', 'Anzeigename für den OIDC-Login-Button'),
('auth.reset.url', '', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'beacf191-2864-439c-987d-b3f331f72bef', 'public', 'URL für das Zurücksetzen von Passwörtern'),
('avatars.type', 'pixelArt', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '187e7d8d-aa6c-4330-aca4-e9d3e88ceae2', 'authenticated', 'Gibt den zu verwendeten Avatar Art an. Siehe https://www.dicebear.com/styles/ für alle Möglichkeiten. Möglichkeiten: "adventurer", "adventurerNeutral", "avataaars", "avataaarsNeutral", "bigEars", "bigEarsNeutral", "bigSmile", "bottts", "botttsNeutral", "croodles", "croodlesNeutral", "dylan", "funEmoji", "glass", "icons", "identicon", "initials", "lorelei", "loreleiNeutral", "micah", "miniavs", "notionists", "notionistsNeutral", "openPeeps", "personas", "pixelArt", "pixelArtNeutral", "rings", "shapes", "thumbs"'),
('branding.app.name', 'OpenVLE', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'aae977a9-4a04-407e-845e-750260c44fdd', 'public', 'Angezeigter Name der Anwendung'),
('branding.app.title', 'OpenVLE', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'ca553a00-733e-4722-973f-0ba7c7869398', 'public', 'Seitentitel der Anwendung'),
('branding.customer.name', 'Example Customer', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'ab7a2f26-209d-49e2-bf4d-71aa3e120376', 'authenticated', 'Name des Kunden für Branding-Zwecke'),
('branding.customer.url01', 'https://www.example.com/my-example-project-page', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'ccc2f7c7-36a9-4c5b-abc8-383fb67f5b9f', 'authenticated', 'Primäre Kunden-URL für Branding'),
('branding.customer.url02', 'https://www.example.com/', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '2381a33d-8a3a-4a9c-afdd-7ca33c4d1db3', 'authenticated', 'Sekundäre Kunden-URL für Branding'),
('branding.docs.url', 'https://docs.openvle.org', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'cf8c4464-c5f7-416b-8023-4dfbadb0b019', 'authenticated', 'URL zur Produktdokumentation'),
('branding.docs.label', 'Dokumentation', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '684a6dad-915e-4fc3-b17b-2ff7fb387f94', 'authenticated', 'Anzeigename für Dokumentationslink'),
('branding.docs.deepurl', 'https://docs.openvle.org', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '817d2900-45c9-478b-a661-6d7f7f7c1e47', 'authenticated', 'Direktlink zu tieferen Dokumentationsseiten'),
('branding.support.email', 'support@example.com', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '7800ab81-b19e-4d60-81c8-80c0b83f8ef5', 'authenticated', 'Support-E-Mail-Adresse'),
('branding.support.url', 'https://www.example.com', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '2530fe2c-fb64-452a-a0b8-641749d4dc35', 'authenticated', 'Support-Webseite'),
('branding.support.name', 'Example GmbH', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1ddcb040-d881-4892-b098-6b7e76ca9527', 'authenticated', 'Name des Supports oder Unternehmens'),
('connection.profiles.username.help', 'Dieser Benutzername ist nicht erlaubt.', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '0f69cb90-1136-4115-896c-7c849a4259a3', 'authenticated', 'Gibt den Hilfetext für nicht erlaubte Benutzernamen bei Verbindungsvorlagen an.'),
('connection.profiles.username.regex', '.*', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '66921961-21e6-4652-8f96-1c51c71a30f0', 'authenticated', 'Regex zur Prüfung der erlaubten Benutzernamen bei Verbindungsvorlagen. Erlaubt im Standard alle Benutzernamen.'),
('events.create.participants.students', '1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '8b065275-9c0c-4861-aca4-9d64e58116c1', 'authenticated', 'Mindestanzahl Teilnehmer vom Typ "Studierende" bei neuen Events'),
('events.create.participants.teachers', '1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '80939068-2b16-4e11-914d-cec124462bfe', 'authenticated', 'Mindestanzahl Teilnehmer vom Typ "Lehrerende" bei neuen Events'),
('events.end.prep_time.days', '7', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '0dcd914c-eb98-42a6-9d98-2f5043a70b78', 'authenticated', 'Anzahl der Tage nach dem Enddatum bis zur automatischen Archivierung der Veranstaltung. **Achtung:** Zusätzliche Anpassung in der Backend `.env` momentan noch erforderlich.'),
('events.schema.connections', '("{convert_to_slug(event.slug, max_length=8)}-temp{template.proxmoxId}-{convert_to_slug(user.username, max_length=10)}-{user.roleName}")[:100]-{connection.protocol}")[:100]', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '87e96e04-9273-47a3-b6f4-dbd684b3c52c', 'internal', 'Namensschema für Verbindungsressourcen bei Events'),
('events.schema.vms', '("{convert_to_slug(event.slug, max_length=8)}-temp{template.proxmoxId}-{convert_to_slug(user.username, max_length=10)}-{user.roleName}")[:100]', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'dc0a84a0-615d-4d08-a5d9-35c4f05f46a8', 'internal', 'Namensschema für virtuelle Maschinen bei Events'),
('events.start.prep_time.days', '7', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'adfc966b-347b-40fb-bc1b-3aa7c3729c33', 'authenticated', 'Anzahl der Tage vor dem Startdatum bis zum automatischen Deployment der Veranstaltung. **Achtung:** Zusätzliche Anpassung in der Backend `.env` momentan noch erforderlich.'),
('features.ldap', 'true', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '2bdbaff3-3d22-4b75-97a1-025a09c11828', 'admins', 'Kennzeichnet, ob LDAP-Integration verfügbar ist'),
('features.email', 'true', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '47c1dd85-c244-4f08-ad97-ac4c0c0f8763', 'admins', 'Kennzeichnet, ob E-Mail-Funktionen aktiviert sind'),
('guacamole.url.base', 'https://guacamole.example.de', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'acc23394-c578-4e73-899f-4e01c2dc9a96', 'authenticated', 'Basis-URL (extern) der verwendeten Guacamole Instanz (z.B. `https://guacamole.example.de`).'),
('maintenance.enabled', 'false', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'bd4e9719-73e9-42b2-ad45-990850edf6d2', 'public', 'Gibt an, ob aktuell ein Wartungsmodus aktiv ist. Bei aktivem Wartungsmodus ist ein Login weiterhin möglich, aber es wird im Frontend ein konstanter Hinweis angezeigt.'),
('maintenance.label', 'Die Anwendung befindet sich aktuell im Wartungsmodus.', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '49ea8f11-f221-4ce2-9ae5-a259a881aaca', 'public', 'Hinweis im Frontend bei aktivem Wartungsmodus der Anwendung (*öffentlich ohne Authentifizierung einsehbar*)'),
('moodle.enabled', 'false', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'd85fe37a-f4f2-4364-8960-8c5ad61c1681', 'authenticated', 'Kennzeichnet, ob Moodle Integration aktiviert ist. **Achtung:** Zusätzliche Anpassung in der Backend `.env` momentan noch erforderlich.'),
('moodle.url.base', 'https://moodle.example.com', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '4e475a6d-80b2-43dc-ac55-c815c0db2bd9', 'authenticated', 'Basis-URL des Moodle Servers'),
('passwords.min', '8', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '0577142c-cdde-4fca-ac46-8f848bf66651', 'authenticated', 'Minimale Passwortlänge'),
('passwords.max', '64', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '63a77583-d98e-4e04-946d-d962891777ad', 'authenticated', 'Maximale Passwortlänge'),
('passwords.lowercase.min', '2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'bbd5b485-9a44-485b-b084-6dff343b9de2', 'authenticated', 'Mindestanzahl an Kleinbuchstaben im Passwort'),
('passwords.uppercase.min', '2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'fc83d85c-242b-4e1b-9020-6424f18b20b4', 'authenticated', 'Mindestanzahl an Großbuchstaben im Passwort'),
('passwords.numbers.min', '2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'c6ce36c4-cb6e-4f21-af8f-e83399dbc38b', 'authenticated', 'Mindestanzahl an Ziffern im Passwort'),
('passwords.special.min', '2', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '48c87c44-7eb7-4f0d-9497-ca8de2a8c945', 'authenticated', 'Mindestanzahl an Sonderzeichen im Passwort'),
('roles.students', 'cec850b3-608b-4cc3-aac2-4adc85df38e3', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'db6fd62d-78d3-4524-87eb-b999300d1459', 'authenticated', 'Rollen-ID für Studierende'),
('roles.teachers', 'acec4438-2dec-41fb-9e5e-f0284845753e', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '523d768b-519d-4f08-9d46-6f6453265ec8', 'authenticated', 'Rollen-ID für Lehrerende'),
('version.backend.label', 'prod', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '7a308d1c-cb62-47f0-9bb3-412272ea3510', 'public', 'Kennzeichnung der Backend-Version'),
('vms.create.cpu.min', '1', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'c655067d-86c8-4359-86f5-cf4f58704251', 'authenticated', 'Minimale CPU-Kerne für VM-Erstellung'),
('vms.create.cpu.max', '12', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'e7a48f4e-ad28-4082-85ba-b98b9faed340', 'authenticated', 'Maximale CPU-Kerne für VM-Erstellung'),
('vms.create.ram.min', '1024', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '9e11e0d2-f69e-46b9-97fb-04a073f27e3f', 'authenticated', 'Minimaler Arbeitsspeicher (MB) für VM-Erstellung'),
('vms.create.ram.max', '20480', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'a30473d0-b200-4728-aa8e-1947a4b685ba', 'authenticated', 'Maximaler Arbeitsspeicher (MB) für VM-Erstellung'),
('vms.create.disk.min', '10', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', 'd8cbfaaa-a97b-4be7-8208-a6327e7923fe', 'authenticated', 'Minimale Festplattengröße (GB) für VM-Erstellung'),
('vms.create.disk.max', '1000', '1970-01-01 00:00:00', '1970-01-01 00:00:00', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '1db3d8ac-22d9-4116-976a-93ad6e4fb234', '9b7ff37b-9cd0-4264-807b-cea13e2501d9', 'authenticated', 'Maximale Festplattengröße (GB) für VM-Erstellung');
