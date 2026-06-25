import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/device.dart';

class CheckResult {
  final bool online;
  final int? pingMs;
  CheckResult(this.online, this.pingMs);
}

class DeviceChecker {
  static const Duration _timeout = Duration(seconds: 2);

  /// Перевіряє пристрій згідно з його режимом ping
  static Future<CheckResult> check(Device device) async {
    switch (device.pingMode) {
      case PingMode.tcp:  return _tcp(device.ip,  device.port);
      case PingMode.http: return _http(device.ip, device.port);
      case PingMode.icmp: return _icmp(device.ip);
    }
  }

  // ── TCP connect ─────────────────────────────────────────────────
  static Future<CheckResult> _tcp(String ip, int port) async {
    final sw = Stopwatch()..start();
    try {
      final sock = await Socket.connect(ip, port, timeout: _timeout);
      final ms = sw.elapsedMilliseconds;
      await sock.close();
      return CheckResult(true, ms);
    } catch (_) {
      return CheckResult(false, null);
    }
  }

  // ── HTTP GET ─────────────────────────────────────────────────────
  static Future<CheckResult> _http(String ip, int port) async {
    final sw = Stopwatch()..start();
    try {
      final res = await http
          .get(Uri.parse('http://$ip:$port/'))
          .timeout(_timeout);
      final ms = sw.elapsedMilliseconds;
      return CheckResult(res.statusCode < 500, ms);
    } catch (_) {
      return CheckResult(false, null);
    }
  }

  // ── ICMP ping (через системну команду) ──────────────────────────
  static Future<CheckResult> _icmp(String ip) async {
    final sw = Stopwatch()..start();
    try {
      // Android: ping -c 1 -W 2 <ip>
      final result = await Process.run(
        'ping',
        ['-c', '1', '-W', '2', ip],
      ).timeout(_timeout + const Duration(seconds: 1));

      final ms = sw.elapsedMilliseconds;
      if (result.exitCode == 0) {
        // Витягуємо час із рядка типу "time=12.3 ms"
        final match = RegExp(r'time[=<]([\d.]+)').firstMatch(result.stdout.toString());
        final parsed = match != null ? double.tryParse(match.group(1)!)?.round() : ms;
        return CheckResult(true, parsed ?? ms);
      }
      return CheckResult(false, null);
    } catch (_) {
      // Якщо ping недоступний — fallback на TCP
      return _tcp(ip, 80);
    }
  }
}
