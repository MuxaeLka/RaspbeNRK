import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/device.dart';
import '../services/device_provider.dart';
import '../widgets/device_card.dart';
import '../widgets/device_dialog.dart';
import '../theme/app_theme.dart';
import 'webview_screen.dart';
import 'log_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _searchCtrl = TextEditingController();
  bool _searchOpen  = false;

  @override
  void dispose() { _searchCtrl.dispose(); super.dispose(); }

  void _openWebView(Device device) =>
    Navigator.push(context, MaterialPageRoute(builder: (_) => WebViewScreen(device: device)));

  Future<void> _showAddDialog() async {
    final provider = context.read<DeviceProvider>();
    final result   = await showDialog<Device>(
      context: context,
      builder: (_) => DeviceDialog(
        ipExists: (ip, {excludeId}) => provider.ipExists(ip, excludeId: excludeId),
      ),
    );
    if (result != null && mounted) provider.addDevice(result);
  }

  Future<void> _showEditDialog(Device device) async {
    final provider = context.read<DeviceProvider>();
    final result   = await showDialog<Device>(
      context: context,
      builder: (_) => DeviceDialog(
        device: device,
        ipExists: (ip, {excludeId}) => provider.ipExists(ip, excludeId: excludeId),
      ),
    );
    if (result != null && mounted) provider.updateDevice(result);
  }

  Future<void> _confirmDelete(Device device) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Видалити пристрій?'),
        content: Text('${device.name} (${device.ip})',
            style: const TextStyle(color: AppTheme.textDim)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Скасувати')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.offline),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Видалити'),
          ),
        ],
      ),
    );
    if (ok == true && mounted) context.read<DeviceProvider>().removeDevice(device);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgDeep,
      appBar: _buildAppBar(),
      body: Consumer<DeviceProvider>(
        builder: (ctx, provider, _) {
          if (provider.loading) {
            return const Center(child: CircularProgressIndicator(color: AppTheme.accent));
          }
          final devices = provider.filteredDevices;
          if (devices.isEmpty) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.devices_other, size: 64, color: AppTheme.textDim),
                const SizedBox(height: 16),
                Text(
                  provider.searchQuery.isEmpty
                      ? 'Немає пристроїв.\nНатисніть + щоб додати.'
                      : 'Нічого не знайдено.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppTheme.textDim, fontSize: 14),
                ),
              ]),
            );
          }
          return RefreshIndicator(
            color: AppTheme.accent,
            backgroundColor: AppTheme.bgPanel,
            onRefresh: () async {
              await Future.wait(devices.map((d) => provider.checkDevice(d)));
            },
            child: GridView.builder(
              padding: const EdgeInsets.all(10),
              // ── 3 колонки ─────────────────────────────────────────
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount:   3,
                childAspectRatio: 0.85,
                mainAxisSpacing:  8,
                crossAxisSpacing: 8,
              ),
              itemCount: devices.length,
              itemBuilder: (_, i) {
                final d = devices[i];
                return DeviceCard(
                  device:      d,
                  onDoubleTap: () => _openWebView(d),
                  onEdit:      () => _showEditDialog(d),
                  onDelete:    () => _confirmDelete(d),
                  onCheck:     () => provider.checkDevice(d),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.btnPrimary,
        foregroundColor: AppTheme.textMain,
        onPressed:       _showAddDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    if (_searchOpen) {
      return AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            setState(() { _searchOpen = false; _searchCtrl.clear(); });
            context.read<DeviceProvider>().setSearch('');
          },
        ),
        title: TextField(
          controller: _searchCtrl,
          autofocus:  true,
          style: const TextStyle(color: AppTheme.textMain, fontSize: 14),
          decoration: const InputDecoration(
            hintText:  'Пошук...',
            border:    InputBorder.none,
            hintStyle: TextStyle(color: AppTheme.textDim),
          ),
          onChanged: (q) => context.read<DeviceProvider>().setSearch(q),
        ),
      );
    }

    return AppBar(
      title: Consumer<DeviceProvider>(
        builder: (_, p, __) {
          final online  = p.devices.where((d) => d.online == true).length;
          final offline = p.devices.where((d) => d.online == false).length;
          return Row(children: [
            const Text('NRK Manager',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const SizedBox(width: 8),
            _badge(online.toString(),  AppTheme.online),
            const SizedBox(width: 4),
            _badge(offline.toString(), AppTheme.offline),
          ]);
        },
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.search, size: 20),
          onPressed: () => setState(() => _searchOpen = true),
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert, size: 20),
          itemBuilder: (_) => [
            _pop('log',      '📋 Журнал подій'),
            _pop('settings', '⚙️ Налаштування'),
          ],
          onSelected: (v) {
            if (v == 'log')
              Navigator.push(context, MaterialPageRoute(builder: (_) => const LogScreen()));
            else if (v == 'settings')
              Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()));
          },
        ),
      ],
    );
  }

  Widget _badge(String text, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(
      color:        color.withOpacity(0.15),
      borderRadius: BorderRadius.circular(10),
      border:       Border.all(color: color.withOpacity(0.4)),
    ),
    child: Text(text, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w700)),
  );

  PopupMenuItem<String> _pop(String v, String t) =>
      PopupMenuItem(value: v, child: Text(t, style: const TextStyle(fontSize: 13)));
}
