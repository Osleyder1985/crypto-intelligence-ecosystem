plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.crypto.intelligence.issue9kotlin"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.crypto.intelligence.issue9kotlin"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // Debug-key signing is for CI emulator installation only, never production distribution.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
