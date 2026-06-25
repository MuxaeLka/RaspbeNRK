# NRK Manager — Flutter Mobile App

Мобільна версія менеджера **Raspberry Pi 5** та **MikroTik** через **WireGuard VPN**.  
Розроблено для **Samsung Galaxy S24 Ultra** (Android).

## Скриншот функціоналу

| Функція | Деталі |
|---------|--------|
| Список пристроїв | Картки у сітці 2×N |
| Автоперевірка | TCP / HTTP / ICMP, кожні 5 сек |
| Онлайн | 🟢 Зелене свічення + час відповіді |
| Офлайн | 🔴 Червоне свічення |
| WebView | Подвійний тап → вбудований браузер |
| CRUD | Додавання / редагування / видалення |
| Типи | Raspberry Pi (8080), MikroTik (80), Custom |
| Зберігання | JSON через SharedPreferences |
| Журнал | Всі зміни статусів і операції |
| Тема | GitHub Dark (`#0d1117`, акцент `#388bfd`) |
| Мова | Українська |

## Пристрої за замовчуванням

| Назва | IP | Порт | Тип |
|-------|----|------|-----|
| NRK-1 | 10.60.93.50 | 8080 | Raspberry Pi |
| NRK-2 | 10.60.93.51 | 8080 | Raspberry Pi |
| ... | ... | ... | ... |
| NRK-7 | 10.60.93.56 | 8080 | Raspberry Pi |

## Встановлення та збірка

### Швидко — завантажити APK з GitHub Releases

1. Перейти в [Releases](../../releases/latest)
2. Завантажити `NRKManager-vX.X.X-arm64-v8a.apk`
3. Встановити через файловий менеджер або ADB:

```bash
adb install NRKManager-vX.X.X-arm64-v8a.apk
```

### Збірка вручну

```bash
# Клонувати репозиторій
git clone https://github.com/MuxaeLka/RaspbeNRK.git
cd RaspbeNRK/nrk_manager_flutter

# Встановити залежності
flutter pub get

# Зібрати APK для arm64 (S24 Ultra)
flutter build apk --release --target-platform android-arm64

# APK буде тут:
# build/app/outputs/flutter-apk/app-release.apk

# Встановити через ADB
adb install build/app/outputs/flutter-apk/app-release.apk
```

### Вимоги для збірки

- Flutter SDK 3.24+ (`flutter --version`)
- Android Studio / Android SDK
- Java 17
- Android NDK (встановлюється автоматично через Flutter)

## Публікація нового релізу через GitHub Actions

```bash
git tag v1.0.1
git push origin v1.0.1
```

GitHub Actions автоматично:
1. Збере APK (arm64, armv7, universal)
2. Опублікує GitHub Release з файлами

## Мережа

Застосунок підключається до пристроїв через **WireGuard VPN**:
- Підмережа: `10.60.93.0/24`
- Сервер VPN: CHR "Aspirin"
- Налаштування WireGuard на телефоні виконується окремо (імпорт конфігу)

## Структура проєкту

```
lib/
  main.dart                  # Точка входу
  theme/
    app_theme.dart           # GitHub Dark тема
  models/
    device.dart              # Модель пристрою (DeviceType, PingMode)
  services/
    device_checker.dart      # TCP/HTTP/ICMP перевірка
    device_provider.dart     # Стан (ChangeNotifier)
    storage_service.dart     # SharedPreferences JSON
    update_checker.dart      # GitHub Releases API
  screens/
    home_screen.dart         # Головний екран (сітка карток)
    webview_screen.dart      # Вбудований браузер
    log_screen.dart          # Журнал подій
    settings_screen.dart     # Налаштування
  widgets/
    device_card.dart         # Картка пристрою з пульсацією
    device_dialog.dart       # Діалог додавання/редагування
```
