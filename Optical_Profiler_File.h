#pragma once
#include "Image3D_File.h"

#include <fstream>

class Optical_Profiler_File :
	public Image3D_File
{
public:
	Optical_Profiler_File() : Image3D_File() {}
	Optical_Profiler_File( const char* file_name ) : Image3D_File() { Open( file_name ); }

	bool Open( const char* file_name );

protected:
	bool Read_Header_Info( std::ifstream & optical_profiler_file, int start_location, int size );

};

