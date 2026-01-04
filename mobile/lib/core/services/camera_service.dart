import 'dart:io';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:image/image.dart' as img;

import '../constants.dart';

class CameraService {
  List<CameraDescription>? _cameras;
  CameraController? _controller;

  Future<void> initialize() async {
    _cameras = await availableCameras();
  }

  List<CameraDescription> get cameras => _cameras ?? [];

  CameraController? get controller => _controller;

  Future<CameraController?> initializeCamera({
    CameraLensDirection direction = CameraLensDirection.back,
    ResolutionPreset resolution = ResolutionPreset.high,
  }) async {
    if (_cameras == null || _cameras!.isEmpty) {
      await initialize();
    }

    final camera = _cameras?.firstWhere(
      (c) => c.lensDirection == direction,
      orElse: () => _cameras!.first,
    );

    if (camera == null) return null;

    _controller = CameraController(
      camera,
      resolution,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );

    await _controller!.initialize();
    return _controller;
  }

  Future<void> dispose() async {
    await _controller?.dispose();
    _controller = null;
  }

  Future<Uint8List?> takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) {
      return null;
    }

    try {
      final XFile file = await _controller!.takePicture();
      final bytes = await file.readAsBytes();

      // Process image
      return processImage(bytes);
    } catch (e) {
      return null;
    }
  }

  /// Process and optimize image
  Uint8List processImage(Uint8List imageBytes) {
    final image = img.decodeImage(imageBytes);
    if (image == null) return imageBytes;

    // Resize if necessary
    img.Image processed = image;
    if (image.width > AppConstants.maxPhotoWidth ||
        image.height > AppConstants.maxPhotoHeight) {
      processed = img.copyResize(
        image,
        width: AppConstants.maxPhotoWidth,
        height: AppConstants.maxPhotoHeight,
        maintainAspect: true,
      );
    }

    // Encode with quality setting
    return Uint8List.fromList(
      img.encodeJpg(processed, quality: AppConstants.photoQuality),
    );
  }

  /// Generate thumbnail
  Uint8List generateThumbnail(Uint8List imageBytes) {
    final image = img.decodeImage(imageBytes);
    if (image == null) return imageBytes;

    final thumbnail = img.copyResize(
      image,
      width: AppConstants.thumbnailSize,
      height: AppConstants.thumbnailSize,
      maintainAspect: true,
    );

    return Uint8List.fromList(img.encodeJpg(thumbnail, quality: 80));
  }
}
