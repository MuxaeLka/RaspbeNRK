import 'package:flutter/material.dart';

class AppTheme {
  // ── Палітра GitHub Dark ────────────────────────────────────────
  static const Color bgDeep     = Color(0xFF0d1117);
  static const Color bgPanel    = Color(0xFF161b22);
  static const Color bgCard     = Color(0xFF161b22);
  static const Color bgRow      = Color(0xFF111820);
  static const Color accent     = Color(0xFF388bfd);
  static const Color accentHover= Color(0xFF58a6ff);
  static const Color online     = Color(0xFF3fb950);
  static const Color offline    = Color(0xFFf85149);
  static const Color warn       = Color(0xFFd29922);
  static const Color textMain   = Color(0xFFe6edf3);
  static const Color textDim    = Color(0xFF8b949e);
  static const Color textAccent = Color(0xFF58a6ff);
  static const Color border     = Color(0xFF30363d);
  static const Color btnBg      = Color(0xFF21262d);
  static const Color btnHover   = Color(0xFF30363d);
  static const Color btnPrimary = Color(0xFF1f6feb);
  static const Color logBg      = Color(0xFF0a0e14);

  static ThemeData get dark => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: bgDeep,
    colorScheme: const ColorScheme.dark(
      surface: bgDeep,
      primary: accent,
      secondary: accentHover,
      error: offline,
      onPrimary: textMain,
      onSurface: textMain,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: bgPanel,
      foregroundColor: textMain,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
      titleTextStyle: TextStyle(
        color: textMain,
        fontSize: 16,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.3,
      ),
    ),
    cardTheme: CardThemeData(
      color: bgCard,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: border, width: 1),
      ),
    ),
    dividerColor: border,
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: bgPanel,
      labelStyle: const TextStyle(color: textDim),
      hintStyle: const TextStyle(color: textDim),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: accent, width: 1.5),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: btnPrimary,
        foregroundColor: textMain,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        elevation: 0,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: textAccent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: textDim),
    ),
    dropdownMenuTheme: DropdownMenuThemeData(
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgPanel,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: accent, width: 1.5),
        ),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: bgPanel,
      contentTextStyle: const TextStyle(color: textMain),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: border),
      ),
      behavior: SnackBarBehavior.floating,
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: bgPanel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: border),
      ),
      titleTextStyle: const TextStyle(color: textMain, fontSize: 16, fontWeight: FontWeight.w600),
      contentTextStyle: const TextStyle(color: textDim, fontSize: 13),
    ),
    textTheme: const TextTheme(
      bodyLarge:  TextStyle(color: textMain,  fontSize: 14),
      bodyMedium: TextStyle(color: textMain,  fontSize: 13),
      bodySmall:  TextStyle(color: textDim,   fontSize: 11),
      labelLarge: TextStyle(color: textMain,  fontSize: 13, fontWeight: FontWeight.w600),
      titleMedium:TextStyle(color: textMain,  fontSize: 14, fontWeight: FontWeight.w600),
      titleSmall: TextStyle(color: textDim,   fontSize: 12),
    ),
    popupMenuTheme: PopupMenuThemeData(
      color: bgPanel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: border),
      ),
      textStyle: const TextStyle(color: textMain, fontSize: 13),
    ),
  );
}
