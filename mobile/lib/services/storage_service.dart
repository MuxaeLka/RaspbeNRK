import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/device.dart';

class StorageService {
  static const _keyDevices = 'nrk_devices';
  static const _keyLog     = 'nrk_log';
  static const _keyVersion = 'nrk_config_version';

  static final List<Device> _defaultDevices = List.generate(
    7,
    (i) => Device(
      id:         'default_nrk_${i + 1}',
      name:       'NRK-${i + 1}',
      ip:         '10.60.93.${50 + i}',
      port:       8080,
      deviceType: DeviceType.raspberry,
      pingMode:   PingMode.tcp,
    ),
  );

  // ── Завантажити пристрої ────────────────────────────────────────
  static Future<List<Device>> loadDevices() async {
    final prefs = await SharedPreferences.getInstance();
    final raw   = prefs.getString(_keyDevices);
    if (raw == null) {
      await saveDevices(_defaultDevices);
      return _defaultDevices;
    }
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list.map((j) => Device.fromJson(j as Map<String, dynamic>)).toList();
    } catch (_) {
      return _defaultDevices;
    }
  }

  // ── Зберегти пристрої ──────────────────────────────────────────
  static Future<void> saveDevices(List<Device> devices) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyDevices, jsonEncode(devices.map((d) => d.toJson()).toList()));
  }

  // ── Журнал подій ───────────────────────────────────────────────
  static Future<List<String>> loadLog() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_keyLog) ?? [];
  }

  static Future<void> saveLog(List<String> entries) async {
    final prefs = await SharedPreferences.getInstance();
    // Зберігаємо останні 500 записів
    final trimmed = entries.length > 500 ? entries.sublist(entries.length - 500) : entries;
    await prefs.setStringList(_keyLog, trimmed);
  }

  static Future<void> clearLog() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyLog);
  }

  // ── Скинути до заводських ──────────────────────────────────────
  static Future<void> resetAll() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
