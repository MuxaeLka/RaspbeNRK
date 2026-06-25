import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/device_provider.dart';
import '../theme/app_theme.dart';

class LogScreen extends StatelessWidget {
  const LogScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgDeep,
      appBar: AppBar(
        title: const Text('Журнал подій'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep, size: 20),
            tooltip: 'Очистити журнал',
            onPressed: () async {
              final ok = await showDialog<bool>(
                context: context,
                builder: (_) => AlertDialog(
                  title: const Text('Очистити журнал?'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Скасувати')),
                    ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Очистити')),
                  ],
                ),
              );
              if (ok == true && context.mounted) {
                context.read<DeviceProvider>().clearLog();
              }
            },
          ),
        ],
      ),
      body: Consumer<DeviceProvider>(
        builder: (_, provider, __) {
          final log = provider.log.reversed.toList();
          if (log.isEmpty) {
            return const Center(
              child: Text('Журнал порожній', style: TextStyle(color: AppTheme.textDim)),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: log.length,
            itemBuilder: (_, i) {
              final e = log[i];
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Час
                    Text(
                      provider.formatTime(e.timestamp),
                      style: const TextStyle(
                        color: AppTheme.textDim,
                        fontSize: 11,
                        fontFamily: 'monospace',
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Повідомлення
                    Expanded(
                      child: Text(
                        e.message,
                        style: TextStyle(
                          color: e.isError ? AppTheme.offline : AppTheme.textMain,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}
