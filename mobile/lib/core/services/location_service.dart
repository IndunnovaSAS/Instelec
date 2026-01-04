import 'package:geolocator/geolocator.dart';

import '../constants.dart';

class LocationService {
  /// Check if location services are enabled and permissions are granted
  Future<bool> checkPermissions() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return false;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return false;
    }

    return true;
  }

  /// Get current position
  Future<Position?> getCurrentPosition() async {
    try {
      final hasPermission = await checkPermissions();
      if (!hasPermission) {
        return null;
      }

      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: AppConstants.locationTimeoutSeconds),
      );
    } catch (e) {
      return null;
    }
  }

  /// Calculate distance between two points in meters
  double calculateDistance(
    double startLat,
    double startLon,
    double endLat,
    double endLon,
  ) {
    return Geolocator.distanceBetween(startLat, startLon, endLat, endLon);
  }

  /// Check if a point is within a certain radius of another point
  bool isWithinRadius(
    double pointLat,
    double pointLon,
    double centerLat,
    double centerLon,
    double radiusMeters,
  ) {
    final distance = calculateDistance(pointLat, pointLon, centerLat, centerLon);
    return distance <= radiusMeters;
  }

  /// Stream position updates
  Stream<Position> getPositionStream() {
    return Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // meters
      ),
    );
  }
}
