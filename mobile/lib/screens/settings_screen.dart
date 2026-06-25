import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/device_provider.dart';
import '../services/storage_service.dart';
import '../services/update_checker.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _checkingUpdate = false;
  String? _updateMsg;

  Future<void> _checkUpdate() async {
    setState(() { _checkingUpdate = true; _updateMsg = null; });
    final info = await UpdateChecker.checkForUpdate();
    setState(() {
      _checkingUpdate = false;
      _updateMsg = info != null
          ? '🎉 Доступно оновлення v${info.version}'
          : '✅ Встановлена остання версія (v1.0.0)';
    });
  }

  Future<void> _resetAll(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Скинути налаштування?'),
        content: const Text(
          'Всі пристрої будуть видалені, буде відновлено список за замовчуванням.',
          style: TextStyle(color: AppTheme.textDim),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Скасувати')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.offline),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Скинути'),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      await StorageService.resetAll();
      if (context.mounted) {
        await context.read<DeviceProvider>().init();
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgDeep,
      appBar: AppBar(title: const Text('Налаштування')),
      body: ListView(
        children: [
          // ── Про застосунок ─────────────────────────────────────
          _section('Про застосунок'),
          _tile(
            icon: Icons.info_outline,
            title: 'Версія',
            subtitle: 'NRK Manager v1.0.0',
          ),
          _tile(
            icon: Icons.code,
            title: 'Репозиторій',
            subtitle: 'github.com/MuxaeLka/RaspbeNRK',
          ),
          _tile(
            icon: Icons.lan,
            title: 'Мережа',
            subtitle: 'WireGuard VPN 10.60.93.0/24',
          ),

          // ── Оновлення ───────────────────────────────────────────
          _section('Оновлення'),
          ListTile(
            leading: const Icon(Icons.system_update_alt, color: AppTheme.accent, size: 20),
            title: const Text('Перевірити оновлення', style: TextStyle(color: AppTheme.textMain, fontSize: 13)),
            subtitle: _updateMsg != null
                ? Text(_updateMsg!, style: const TextStyle(color: AppTheme.textDim, fontSize: 11))
                : null,
            trailing: _checkingUpdate
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.accent))
                : const Icon(Icons.chevron_right, color: AppTheme.textDim, size: 18),
            onTap: _checkingUpdate ? null : _checkUpdate,
          ),

          // ── Дані ────────────────────────────────────────────────
          _section('Дані'),
          ListTile(
            leading: const Icon(Icons.restore, color: AppTheme.warn, size: 20),
            title: const Text('Скинути до заводських', style: TextStyle(color: AppTheme.textMain, fontSize: 13)),
            subtitle: const Text('Відновить NRK-1..7 за замовчуванням',
                style: TextStyle(color: AppTheme.textDim, fontSize: 11)),
            trailing: const Icon(Icons.chevron_right, color: AppTheme.textDim, size: 18),
            onTap: () => _resetAll(context),
          ),

          // ── Підключення ─────────────────────────────────────────
          _section('Підключення'),
          _tile(
            icon: Icons.timer_outlined,
            title: 'Інтервал перевірки',
            subtitle: '5 секунд (фіксовано)',
          ),
          _tile(
            icon: Icons.access_time,
            title: 'Таймаут підключення',
            subtitle: '2 секунди',
          ),
        ],
      ),
    );
  }

  Widget _section(String title) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 20, 16, 4),
    child: Text(title.toUpperCase(),
      style: const TextStyle(
        color: AppTheme.accent,
        fontSize: 10,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.2,
      ),
    ),
  );

  Widget _tile({required IconData icon, required String title, required String subtitle}) =>
      ListTile(
        leading: Icon(icon, color: AppTheme.textDim, size: 20),
        title: Text(title, style: const TextStyle(color: AppTheme.textMain, fontSize: 13)),
        subtitle: Text(subtitle, style: const TextStyle(color: AppTheme.textDim, fontSize: 11)),
      );
}
