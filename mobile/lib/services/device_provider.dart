import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/device.dart';
import '../services/device_checker.dart';
import '../services/storage_service.dart';
import 'package:intl/intl.dart';

class DeviceProvider extends ChangeNotifier {
  List<Device>   _devices = [];
  List<LogEntry> _log     = [];
  bool           _loading = true;
  Timer?         _timer;
  String         _searchQuery = '';
  bool           _checking = false;

  List<Device>   get devices     => _devices;
  List<LogEntry> get log         => _log;
  bool           get loading     => _loading;
  String         get searchQuery => _searchQuery;

  List<Device> get filteredDevices {
    if (_searchQuery.isEmpty) return _devices;
    final q = _searchQuery.toLowerCase();
    return _devices.where((d) =>
      d.name.toLowerCase().contains(q) ||
      d.ip.toLowerCase().contains(q) ||
      d.deviceType.label.toLowerCase().contains(q)
    ).toList();
  }

  // ── Ініціалізація ──────────────────────────────────────────────
  Future<void> init() async {
    _devices = await StorageService.loadDevices();
    final rawLog = await StorageService.loadLog();
    _log = rawLog.map((s) {
      final parts = s.split('|');
      return LogEntry(
        timestamp: DateTime.tryParse(parts[0]) ?? DateTime.now(),
        message:   parts.length > 1 ? parts.sublist(1).join('|') : s,
        isError:   parts.length > 2 && parts[2] == 'error',
      );
    }).toList();
    _loading = false;
    notifyListeners();

    // Одразу перевіряємо всі
    _checkAll();
    // Автоперевірка кожні 5 секунд
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _checkAll());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ── Пошук ────────────────────────────────────────────────────────
  void setSearch(String q) {
    _searchQuery = q;
    notifyListeners();
  }

  // ── Перевірка доступності ─────────────────────────────────────
  Future<void> _checkAll() async {
    if (_checking) return;
    _checking = true;
    final futures = _devices.map((d) => _checkOne(d)).toList();
    await Future.wait(futures);
    _checking = false;
    notifyListeners();
  }

  Future<void> _checkOne(Device device) async {
    final result = await DeviceChecker.check(device);
    final wasOnline = device.online;
    device.online      = result.online;
    device.pingMs      = result.pingMs;
    device.lastChecked = DateTime.now();

    // Лог зміни статусу
    if (wasOnline != result.online) {
      final status = result.online ? 'ОНЛАЙН' : 'ОФЛАЙН';
      _addLog('${device.name} (${device.ip}) → $status', isError: !result.online);
    }
  }

  Future<void> checkDevice(Device device) async {
    await _checkOne(device);
    notifyListeners();
  }

  // ── CRUD ────────────────────────────────────────────────────────
  Future<void> addDevice(Device device) async {
    _devices.add(device);
    _addLog('Додано: ${device.name} (${device.ip}:${device.port}) [${device.deviceType.label}]');
    await StorageService.saveDevices(_devices);
    notifyListeners();
    _checkOne(device).then((_) => notifyListeners());
  }

  Future<void> updateDevice(Device updated) async {
    final idx = _devices.indexWhere((d) => d.id == updated.id);
    if (idx == -1) return;
    _devices[idx] = updated;
    _addLog('Змінено: ${updated.name} (${updated.ip}:${updated.port})');
    await StorageService.saveDevices(_devices);
    notifyListeners();
    _checkOne(updated).then((_) => notifyListeners());
  }

  Future<void> removeDevice(Device device) async {
    _devices.removeWhere((d) => d.id == device.id);
    _addLog('Видалено: ${device.name} (${device.ip})');
    await StorageService.saveDevices(_devices);
    notifyListeners();
  }

  bool ipExists(String ip, {String? excludeId}) {
    return _devices.any((d) => d.ip == ip && d.id != excludeId);
  }

  // ── Журнал ───────────────────────────────────────────────────────
  void _addLog(String message, {bool isError = false}) {
    _log.add(LogEntry(
      timestamp: DateTime.now(),
      message:   message,
      isError:   isError,
    ));
    // Зберігаємо в фоні
    StorageService.saveLog(
      _log.map((e) => '${e.timestamp.toIso8601String()}|${e.message}|${e.isError ? 'error' : 'ok'}').toList(),
    );
  }

  Future<void> clearLog() async {
    _log.clear();
    await StorageService.clearLog();
    notifyListeners();
  }

  String formatTime(DateTime dt) => DateFormat('HH:mm:ss').format(dt);
}
