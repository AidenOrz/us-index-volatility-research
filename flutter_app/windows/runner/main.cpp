#include <flutter/dart_project.h>
#include <flutter/flutter_view_controller.h>
#include <windows.h>

#include "flutter_window.h"
#include "utils.h"

int APIENTRY wWinMain(_In_ HINSTANCE instance, _In_opt_ HINSTANCE prev,
                      _In_ wchar_t *command_line, _In_ int show_command) {
  // Attach to console when present (e.g., 'flutter run') or create a
  // new console when running with a debugger.
  if (!::AttachConsole(ATTACH_PARENT_PROCESS) && ::IsDebuggerPresent()) {
    CreateAndAttachConsole();
  }

  // Initialize COM, so that it is available for use in the library and/or
  // plugins.
  ::CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

  flutter::DartProject project(L"data");

  std::vector<std::string> command_line_arguments =
      GetCommandLineArguments();

  project.set_dart_entrypoint_arguments(std::move(command_line_arguments));

  FlutterWindow window(project);
  Win32Window::Point origin(10, 10);
  // Work out a size that actually fits: the runner is DPI-aware, so a logical
  // size gets multiplied by scale/96. Take the work area in physical pixels and
  // divide it back out, otherwise a 150% display pushes the window off-screen.
  RECT work{};
  if (!::SystemParametersInfo(SPI_GETWORKAREA, 0, &work, 0)) {
    work = {0, 0, 1707, 1067};
  }
  UINT dpi = ::GetDpiForWindow(::GetDesktopWindow());
  if (dpi == 0) dpi = 96;
  const double k = static_cast<double>(dpi) / 96.0;
  int w = static_cast<int>(((work.right - work.left) - 24) / k);
  int h = static_cast<int>(((work.bottom - work.top) - 24) / k);
  if (w < 900) w = 900;
  if (h < 620) h = 620;
  Win32Window::Size size(w, h);
  // Window title is written as UTF-16 escapes on purpose: MSVC reads .cpp as
  // GBK (codepage 936) here, so literal CJK would raise C4819 and fail the build.
  if (!window.Create(L"\u6CE2\u52A8\u7387\u770B\u76D8", origin, size)) {
    return EXIT_FAILURE;
  }
  window.SetQuitOnClose(true);

  ::MSG msg;
  while (::GetMessage(&msg, nullptr, 0, 0)) {
    ::TranslateMessage(&msg);
    ::DispatchMessage(&msg);
  }

  ::CoUninitialize();
  return EXIT_SUCCESS;
}
