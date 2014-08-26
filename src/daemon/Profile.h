// Copyright (c) 2012 by István Váradi

// This file is part of JSProg, a joystick programming utility

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#ifndef JSPROG_PROFILE_H
#define JSPROG_PROFILE_H
//------------------------------------------------------------------------------

#include "Control.h"

#include <string>

//------------------------------------------------------------------------------

typedef struct _xmlDoc xmlDoc;
typedef struct _xmlNode xmlNode;

//------------------------------------------------------------------------------

/**
 * Wrapper for the XML document representing the profile. It tries to
 * hide the actual XML implementation used.
 */
class Profile
{
private:
    /**
     * Type for a node predicate.
     */
    typedef bool (*nodePredicate_t)(xmlNode* node, void* data);

    /**
     * Parse the file with the given name into an XML document. It
     * also checks the document if it has the right structure.
     *
     * @return the document, if everything is OK
     */
    static xmlDoc* parseFile(const char* filename);

    /**
     * Parse the given string into an XML document. It
     * also checks the document if it has the right structure.
     *
     * @return the document, if everything is OK
     */
    static xmlDoc* parseString(const char* s);

    /**
     * Node predicate: returns whether the given node has the name
     * stored as a const char* in the data.
     */
    static bool isNodeNamed(xmlNode* node, void* data);

    /**
     * Node predicate: returns whether the given node's name is that
     * of a control's node.
     */
    static bool isNodeControl(xmlNode* node, void* data);

    /**
     * Find a node starting from the given one that matches the
     * predicate.
     */
    static xmlNode* findNode(xmlNode* node,
                             nodePredicate_t predicate, void* data);

    /**
     * Find a node with the given name starting from the given other
     * node.
     */
    static xmlNode* findNode(xmlNode* node, const char* name);

    /**
     * Extract the text from the given node and its siblings.
     */
    static bool extractText(std::string& text, xmlNode* node);

    /**
     * Extract the attribute with the given name from the given node.
     */
    static bool extractAttr(std::string& text, xmlNode* node,
                            const char* name);

private:
    /**
     * The XML document representing the profile.
     */
    xmlDoc* doc;

    /**
     * The next node to check for a control.
     */
    mutable xmlNode* nextControl;

public:
    /**
     * Construct the profile for the given file name or string.
     */
    Profile(const char* fileNameOrString, bool isFileName = true);

    /**
     * Destroy the profile.
     */
    ~Profile();

    /**
     * Determine if the profile is valid.
     */
    operator bool() const;

    /**
     * Get the contents of the prologue.
     *
     * @param luaCode will contain the Lua code of the prologue
     *
     * @return whether there was a prologue
     */
    bool getPrologue(std::string& luaCode) const;

    /**
     * Reset the pointer to the next control.
     */
    void resetControls() const;

    /**
     * Get the values associated with the next control, if any
     *
     * @param type will contain the control's type
     * @param code will contain the code of the control
     * @param luaCode will contain the Lua code for the control
     */
    bool getNextControl(Control::type_t& type, int& code, std::string& luaCode) const;

    /**
     * Get the contents of the epilogue.
     *
     * @param luaCode will contain the Lua code of the epilogue
     *
     * @return whether there was an epilogue
     */
    bool getEpilogue(std::string& luaCode) const;
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Profile::operator bool() const
{
    return doc!=0;
}

//------------------------------------------------------------------------------
#endif // JSPROG_PROFILE_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
