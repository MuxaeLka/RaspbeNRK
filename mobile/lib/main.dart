import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'services/device_provider.dart';
import 'screens/home_screen.dart';
import 'theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Примусово portrait (або обидві — для S24 Ultra зручніше)
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.landscapeLeft,
    DeviceOrientation.landscapeRight,
  ]);

  // Прозора status bar
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor:       Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: AppTheme.bgDeep,
    systemNavigationBarIconBrightness: Brightness.light,
  ));

  runApp(
    ChangeNotifierProvider(
      create: (_) => DeviceProvider()..init(),
      child: const NrkManagerApp(),
    ),
  );
}

class NrkManagerApp extends StatelessWidget {
  const NrkManagerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title:        'NRK Manager',
      theme:        AppTheme.dark,
      debugShowCheckedModeBanner: false,
      home:         const HomeScreen(),
    );
  }
}
