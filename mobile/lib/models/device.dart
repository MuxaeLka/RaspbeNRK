import 'package:flutter/material.dart';

enum DeviceType { raspberry, mikrotik, custom }
enum PingMode   { tcp, http, icmp }

extension DeviceTypeExt on DeviceType {
  String get label {
    switch (this) {
      case DeviceType.raspberry: return 'Raspberry Pi';
      case DeviceType.mikrotik:  return 'MikroTik';
      case DeviceType.custom:    return 'Custom';
    }
  }
  String get key {
    switch (this) {
      case DeviceType.raspberry: return 'raspberry';
      case DeviceType.mikrotik:  return 'mikrotik';
      case DeviceType.custom:    return 'custom';
    }
  }
  int get defaultPort {
    switch (this) {
      case DeviceType.raspberry: return 8080;
      case DeviceType.mikrotik:  return 80;
      case DeviceType.custom:    return 80;
    }
  }
}

extension PingModeExt on PingMode {
  String get label {
    switch (this) {
      case PingMode.tcp:  return 'TCP connect';
      case PingMode.http: return 'HTTP GET';
      case PingMode.icmp: return 'ICMP ping';
    }
  }
  String get key {
    switch (this) {
      case PingMode.tcp:  return 'tcp';
      case PingMode.http: return 'http';
      case PingMode.icmp: return 'icmp';
    }
  }
}

class Device {
  String     id;
  String     name;
  String     ip;
  int        port;
  DeviceType deviceType;
  PingMode   pingMode;

  // Налаштування свічення
  String? glowColorHex;  // напр. '#3fb950'
  double? glowWidth;     // напр. 12.0

  // Стан (не зберігається)
  bool?    online;
  int?     pingMs;
  DateTime? lastChecked;

  Device({
    required this.id,
    required this.name,
    required this.ip,
    required this.port,
    this.deviceType    = DeviceType.raspberry,
    this.pingMode      = PingMode.tcp,
    this.glowColorHex,
    this.glowWidth,
    this.online,
    this.pingMs,
    this.lastChecked,
  });

  String get webUrl => 'http://$ip:$port';

  Map<String, dynamic> toJson() => {
    'id':            id,
    'name':          name,
    'ip':            ip,
    'port':          port,
    'device_type':   deviceType.key,
    'ping_mode':     pingMode.key,
    'glow_color':    glowColorHex,
    'glow_width':    glowWidth,
  };

  factory Device.fromJson(Map<String, dynamic> j) {
    DeviceType dt;
    switch (j['device_type'] as String? ?? 'raspberry') {
      case 'mikrotik': dt = DeviceType.mikrotik; break;
      case 'custom':   dt = DeviceType.custom;   break;
      default:         dt = DeviceType.raspberry;
    }
    PingMode pm;
    switch (j['ping_mode'] as String? ?? 'tcp') {
      case 'http': pm = PingMode.http; break;
      case 'icmp': pm = PingMode.icmp; break;
      default:     pm = PingMode.tcp;
    }
    return Device(
      id:           j['id']   as String? ?? 'dev_${DateTime.now().millisecondsSinceEpoch}',
      name:         j['name'] as String,
      ip:           j['ip']   as String,
      port:         (j['port'] as num).toInt(),
      deviceType:   dt,
      pingMode:     pm,
      glowColorHex: j['glow_color'] as String?,
      glowWidth:    (j['glow_width'] as num?)?.toDouble(),
    );
  }

  Device copyWith({
    String? name, String? ip, int? port,
    DeviceType? deviceType, PingMode? pingMode,
    String? glowColorHex, double? glowWidth,
  }) => Device(
    id:           id,
    name:         name          ?? this.name,
    ip:           ip            ?? this.ip,
    port:         port          ?? this.port,
    deviceType:   deviceType    ?? this.deviceType,
    pingMode:     pingMode      ?? this.pingMode,
    glowColorHex: glowColorHex  ?? this.glowColorHex,
    glowWidth:    glowWidth     ?? this.glowWidth,
  );
}

class LogEntry {
  final DateTime timestamp;
  final String   message;
  final bool     isError;
  LogEntry({required this.timestamp, required this.message, this.isError = false});
}
